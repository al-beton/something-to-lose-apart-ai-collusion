# Implements: ci/report-comment
"""report-comment: keep one comment on the pull request with the game's report.

Usage: `python3 .github/scripts/report_comment.py FIRST_SCREEN_MD`, inside the
blocking-checks report job, after `configs/pr-game.yaml` was played and its
report built. REPORT_URL links the full page (the uploaded artifact). The
comment starts with a hidden marker, so each push edits the same comment.
Needs GITHUB_TOKEN (pull-requests: write), GITHUB_REPOSITORY and
GITHUB_EVENT_PATH.

Posting is best effort: a pull request from a fork gets a read-only token,
so a refused call prints a warning and exits 0. The game and the report are
what the checks stand on; the comment is only the readable view.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

MARKER = "<!-- pr-report -->"
API = "https://api.github.com"


def comment_body(screen, sha, link):
    return (
        f"{MARKER}\n### What the lab does at `{sha[:7]}`\n\n"
        "One free game of scripted firms (`configs/pr-game.yaml`), "
        f"[full report]({link}).\n\n{screen.strip()}\n"
    )


def existing_comment(comments):
    """The id of the report comment already on the pull request, if any."""
    return next((c["id"] for c in comments if c["body"].startswith(MARKER)), None)


def publish(api, repo, number, body):
    """Edit the pull request's report comment, or post it if there is none.

    `api(method, path, payload=None)` makes one GitHub API call and returns its
    JSON; the script passes a real one, tests pass a fake.
    """
    comments = api("GET", f"/repos/{repo}/issues/{number}/comments?per_page=100")
    found = existing_comment(comments)
    if found:
        api("PATCH", f"/repos/{repo}/issues/comments/{found}", {"body": body})
    else:
        api("POST", f"/repos/{repo}/issues/{number}/comments", {"body": body})


def github(token):
    """A GitHub API caller using the given token, standard library only."""

    def call(method, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(API + path, data=data, method=method)
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/vnd.github+json")
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read() or "null")

    return call


def main(screen, link, pull, repo, api):
    if pull is None:
        print("No pull request in this event; nothing to post.")
        return 0
    body = comment_body(screen, pull["head"]["sha"], link)
    try:
        publish(api, repo, pull["number"], body)
    except (urllib.error.URLError, OSError) as error:
        print(f"::warning title=report-comment::Couldn't post the comment: {error}")
        return 0
    print("Posted the report comment.")
    return 0


if __name__ == "__main__":
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
        event_pull = json.load(handle).get("pull_request")
    sys.exit(
        main(
            Path(sys.argv[1]).read_text(),
            os.environ.get("REPORT_URL", ""),
            event_pull,
            os.environ["GITHUB_REPOSITORY"],
            github(os.environ["GITHUB_TOKEN"]),
        )
    )
