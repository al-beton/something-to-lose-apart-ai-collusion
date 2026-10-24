# Implements: ci/smoke-evidence
"""smoke-comment: post the smoke run's summary table on the pull request.

Usage: `python3 .github/scripts/smoke_comment.py TABLE_FILE`, inside the
blocking-checks smoke job. The comment starts with a hidden marker, so each
push edits the same comment instead of adding a new one. Needs GITHUB_TOKEN
(with pull-requests: write), GITHUB_REPOSITORY and GITHUB_EVENT_PATH; events
without a pull request have nothing to post.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

MARKER = "<!-- smoke-run -->"
API = "https://api.github.com"


def comment_body(table, sha):
    return (
        f"{MARKER}\n### Smoke run\n\n"
        f"Free mock agents playing `configs/smoke.yaml` at `{sha[:7]}`:\n\n"
        f"{table}\n"
    )


def existing_comment(comments):
    """The id of the smoke-run comment already on the pull request, if any."""
    return next((c["id"] for c in comments if c["body"].startswith(MARKER)), None)


def publish(api, repo, number, body):
    """Edit the pull request's smoke-run comment, or post it if there is none.

    `api(method, path, payload=None)` makes one GitHub API call and returns its
    JSON; main passes a real one, tests pass a fake.
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


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
        pull = json.load(handle).get("pull_request")
    if pull is None:
        print("No pull request in this event; nothing to post.")
        return 0
    body = comment_body(Path(sys.argv[1]).read_text().strip(), pull["head"]["sha"])
    api = github(os.environ["GITHUB_TOKEN"])
    publish(api, os.environ["GITHUB_REPOSITORY"], pull["number"], body)
    print("Posted the smoke-run summary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
