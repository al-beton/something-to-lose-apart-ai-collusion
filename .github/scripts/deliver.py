"""deliver: the mechanical steps of the deliver-issue skill.

Implements: workflow/one-routine, commits/named-paths, review/review-finished, merging/stacked-retarget, merging/main-stays-green, merging/merge-when-clean

Usage: `python3 .github/scripts/deliver.py <command> ...`

- `commit -m SUBJECT [-m BODY ...] [--runs] PATH ...` stages exactly the
  paths named and commits only them. It refuses `.`, `-A` and anything under
  `runs/` (generated output) unless `--runs` says so on purpose.
- `request-review PR [--note TEXT]` asks Codex to review, pointing it at the
  review-pr skill.
- `wait-review PR [--timeout SECONDS]` waits until Codex has finished
  reviewing the pull request's latest commit, then prints the unresolved
  threads. Codex edits one summary comment in place; its hidden
  `codex-review-state:v1` JSON says what is running, so the first bot comment
  (or a 👀) never counts as a result. Exits 0 with no open threads, 2 with
  some, 1 on timeout.
- `threads PR` prints the unresolved review threads as JSON lines.
- `resolve THREAD_ID REPLY` replies in a thread, then resolves it.
- `merge PR` squash-merges when blocking-checks is green, Codex has finished
  reviewing the latest commit and every thread is resolved, keeping the
  closing block. Pull requests stacked on its branch
  move to main first, the branch is deleted on the remote only (a worktree
  can't check out main), and main's checks run again and must pass.

Standard library only; it drives `gh` and `git`. Functions take `run(*args)`
(a `gh` command, or `git ...` when the first word is "git") and return what
it printed, so tests pass a fake.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import PurePosixPath

STATE = re.compile(r"codex-review-state:v1 (\{.*?\}) -->")
CLOSING = re.compile(r"^(?:Closes|Fixes|Resolves|Part of|Refs|Towards) #\d+$")
REVIEW_REQUEST = (
    "@codex review\n\n"
    "Please follow `.agents/skills/review-pr/SKILL.md`: spec first, then the "
    "tests listed for each statement, then how it is built, with each finding "
    "inline. Be adversarial about clear, extendable code, and skip edge cases "
    "this prototype doesn't need yet."
)
THREADS = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes { id isResolved path line comments(first: 1) {
          nodes { author { login } body } } }
      }
    }
  }
}
"""
RESOLVE = """
mutation($thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(
    input: {pullRequestReviewThreadId: $thread, body: $body}) { comment { id } }
  resolveReviewThread(input: {threadId: $thread}) { thread { isResolved } }
}
"""


class MergeRefused(RuntimeError):
    """A merge condition failed; the message says which."""


def run_command(*args):
    command = list(args) if args[0] == "git" else ["gh", *args]
    done = subprocess.run(
        command, check=False, capture_output=True, text=True, stdin=subprocess.DEVNULL
    )
    if done.returncode:
        sys.exit(f"{' '.join(command[:3])} failed:\n{done.stderr.strip()}")
    return done.stdout


def unsafe_paths(paths, allow_runs=False):
    """Paths a commit must not stage: everything at once, or run output."""
    unsafe = []
    for path in paths:
        parts = PurePosixPath(path).parts
        everything = path in (".", "-A", "--all", "*") or not parts
        if everything or (parts[0] == "runs" and not allow_runs):
            unsafe.append(path)
    return unsafe


def commit(paths, messages, allow_runs=False, run=run_command):
    if not paths:
        sys.exit("Name the paths to commit.")
    if bad := unsafe_paths(paths, allow_runs):
        sys.exit(f"Refusing to stage {bad}: name files, and pass --runs for runs/.")
    run("git", "add", "--", *paths)
    # --only: anything else already staged stays staged, out of this commit.
    run(
        "git",
        "commit",
        *[a for m in messages for a in ("-m", m)],
        "--only",
        "--",
        *paths,
    )


def review_state(comments):
    """The latest Codex code-review state, or None before Codex has replied."""
    state = None
    for comment in comments:
        if match := STATE.search(comment["body"]):
            state = json.loads(match.group(1))["code_review"]
    return state


def review_finished(state, head):
    return (
        bool(state)
        and state["commit_sha"] == head
        and state["status"]
        not in (
            None,
            "running",
        )
    )


def closing_lines(body):
    """The pull request's closing block: one line per issue."""
    return [line for line in body.splitlines() if CLOSING.match(line.strip())]


def unresolved_threads(number, run=run_command):
    repo = json.loads(run("repo", "view", "--json", "owner,name"))
    data = json.loads(
        run(
            "api",
            "graphql",
            "-f",
            f"query={THREADS}",
            "-F",
            f"owner={repo['owner']['login']}",
            "-F",
            f"name={repo['name']}",
            "-F",
            f"number={number}",
        )
    )
    nodes = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    return [t for t in nodes if not t["isResolved"]]


def request_review(number, note="", run=run_command):
    body = REVIEW_REQUEST + (f"\n\n{note}" if note else "")
    run("pr", "comment", str(number), "--body", body)


def wait_review(number, timeout=900, every=30, run=run_command):
    """Wait for a finished review of the head commit; return open threads."""
    head = _view(number, run)["headRefOid"]
    deadline = time.monotonic() + timeout
    while True:
        state = review_state(_comments(number, run))
        print(time.strftime("%H:%M:%S"), state, flush=True)
        if review_finished(state, head):
            return unresolved_threads(number, run)
        if time.monotonic() > deadline:
            return None
        time.sleep(every)


def resolve(thread, reply, run=run_command):
    run(
        "api",
        "graphql",
        "-f",
        f"query={RESOLVE}",
        "-F",
        f"thread={thread}",
        "-f",
        f"body={reply}",
    )


def merge(number, run=run_command, pause=time.sleep):
    pr = _view(number, run)
    checks = run("pr", "checks", str(number))
    if not re.search(r"^blocking-checks\tpass\b", checks, re.MULTILINE):
        raise MergeRefused("blocking-checks isn't green.")
    if not review_finished(review_state(_comments(number, run)), pr["headRefOid"]):
        raise MergeRefused("Codex hasn't finished reviewing the latest commit.")
    if open_threads := unresolved_threads(number, run):
        raise MergeRefused(f"{len(open_threads)} review threads are unresolved.")
    closing = closing_lines(pr["body"])
    if not closing:
        raise MergeRefused("The description has no closing block.")
    branch = pr["headRefName"]
    stacked = json.loads(
        run("pr", "list", "--base", branch, "--state", "open", "--json", "number")
    )
    for child in stacked:
        run("pr", "edit", str(child["number"]), "--base", "main")
    run(
        "pr",
        "merge",
        str(number),
        "--squash",
        "--subject",
        pr["title"],
        "--body",
        "\n".join(closing),
    )
    run("git", "push", "origin", "--delete", branch)
    run("workflow", "run", "blocking-checks.yml", "--ref", "main")
    pause(5)  # let the dispatched run appear in the list
    runs = json.loads(
        run(
            "run",
            "list",
            "--workflow",
            "blocking-checks.yml",
            "--branch",
            "main",
            "--event",
            "workflow_dispatch",
            "--limit",
            "1",
            "--json",
            "databaseId",
        )
    )
    run("run", "watch", str(runs[0]["databaseId"]), "--exit-status")


def _comments(number, run):
    return json.loads(
        run("api", f"repos/{{owner}}/{{repo}}/issues/{number}/comments", "--paginate")
    )


def _view(number, run):
    fields = "number,title,body,headRefName,baseRefName,headRefOid"
    return json.loads(run("pr", "view", str(number), "--json", fields))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="deliver")
    commands = parser.add_subparsers(dest="command", required=True)
    c = commands.add_parser("commit")
    c.add_argument("-m", dest="messages", action="append", required=True)
    c.add_argument("--runs", action="store_true", help="allow paths under runs/")
    c.add_argument("paths", nargs="+")
    r = commands.add_parser("request-review")
    r.add_argument("pr", type=int)
    r.add_argument("--note", default="")
    w = commands.add_parser("wait-review")
    w.add_argument("pr", type=int)
    w.add_argument("--timeout", type=int, default=900)
    t = commands.add_parser("threads")
    t.add_argument("pr", type=int)
    s = commands.add_parser("resolve")
    s.add_argument("thread")
    s.add_argument("reply")
    m = commands.add_parser("merge")
    m.add_argument("pr", type=int)
    args = parser.parse_args(argv)

    if args.command == "commit":
        commit(args.paths, args.messages, args.runs)
    elif args.command == "request-review":
        request_review(args.pr, args.note)
    elif args.command in ("wait-review", "threads"):
        if args.command == "threads":
            threads = unresolved_threads(args.pr)
        else:
            threads = wait_review(args.pr, args.timeout)
        if threads is None:
            print("Timed out: the review is still running.")
            return 1
        for thread in threads:
            print(json.dumps(thread))
        return 2 if threads else 0
    elif args.command == "resolve":
        resolve(args.thread, args.reply)
    elif args.command == "merge":
        try:
            merge(args.pr)
        except MergeRefused as refused:
            print(f"Not merged: {refused}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
