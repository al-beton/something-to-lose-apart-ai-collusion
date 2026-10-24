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


def _call(method, url, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read() or "null")


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
        pull = json.load(handle).get("pull_request")
    if pull is None:
        print("No pull request in this event; nothing to post.")
        return 0
    token, repo = os.environ["GITHUB_TOKEN"], os.environ["GITHUB_REPOSITORY"]
    body = comment_body(Path(sys.argv[1]).read_text().strip(), pull["head"]["sha"])
    issue = f"{API}/repos/{repo}/issues/{pull['number']}/comments"
    found = existing_comment(_call("GET", f"{issue}?per_page=100", token))
    if found:
        _call(
            "PATCH",
            f"{API}/repos/{repo}/issues/comments/{found}",
            token,
            {"body": body},
        )
    else:
        _call("POST", issue, token, {"body": body})
    print("Posted the smoke-run summary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
