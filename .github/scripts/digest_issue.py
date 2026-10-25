# Implements: ci/results-digest
"""digest-issue: keep one "Results digest" issue up to date from main.

Usage: `python3 .github/scripts/digest_issue.py DIGEST_MD`, inside the
blocking-checks job on a push to main, after `lab digest` wrote every
registered experiment's results. The issue titled TITLE is edited in place,
or opened (and pinned, if the token may) when there is none, so the latest
results are always one click away. Needs GITHUB_TOKEN (issues: write) and
GITHUB_REPOSITORY. Best effort, like the pull request comment: a refused call
prints a warning and exits 0.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

TITLE = "Results digest"
API = "https://api.github.com"
LIMIT = 65_000  # characters; an issue body takes at most 65,536


def publish(api, repo, body):
    """Edit the digest issue's body, or open the issue if there is none."""
    body = body[:LIMIT]
    issues = api("GET", f"/repos/{repo}/issues?state=open&per_page=100")
    found = next((i for i in issues if i["title"] == TITLE), None)
    if found:
        api("PATCH", f"/repos/{repo}/issues/{found['number']}", {"body": body})
        return
    made = api("POST", f"/repos/{repo}/issues", {"title": TITLE, "body": body})
    pin = "mutation($id: ID!) { pinIssue(input: {issueId: $id}) { issue { number } } }"
    try:
        api("POST", "/graphql", {"query": pin, "variables": {"id": made["node_id"]}})
    except (urllib.error.URLError, OSError, KeyError):
        print("::warning title=digest-issue::Opened the issue; pin it by hand.")


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


def main(body, repo, api):
    try:
        publish(api, repo, body)
    except (urllib.error.URLError, OSError) as error:
        print(f"::warning title=digest-issue::Couldn't update the issue: {error}")
        return 0
    print(f"Updated the {TITLE} issue.")
    return 0


if __name__ == "__main__":
    sys.exit(
        main(
            Path(sys.argv[1]).read_text(),
            os.environ["GITHUB_REPOSITORY"],
            github(os.environ["GITHUB_TOKEN"]),
        )
    )
