# Implements: pull-requests/closing-block, pull-requests/three-types, pull-requests/title-shows-type-and-issues, specs-and-docs/areas
"""pr-gate: pull request titles and closing blocks follow the rules.

Title: `<feat|fix|improve>(<area>): <summary> (#<n>[, #<m>])`, where the area is a
spec file name. Description: at least one closing-block line (a keyword and issue
numbers), naming every issue in the title. The statements are in
contributing/spec/pull-requests.md; the open-pr skill explains them. Runs inside
blocking-checks; events without a pull request have nothing to check.
"""

import difflib
import json
import os
import re
import sys
from pathlib import Path

from spec_check import DOMAINS, areas

TYPES = ("feat", "fix", "improve")
_ISSUE = r"#\d+"
_TITLE = re.compile(
    rf"^(?P<type>[a-z]+)\((?P<area>[a-z0-9-]+)\): (?P<summary>\S.*?) "
    rf"\((?P<issues>{_ISSUE}(?:, {_ISSUE})*)\)$"
)
# GitHub closes issues named after the first three on merge; the rest only link.
_KEYWORDS = r"closes|fixes|resolves|part of|refs|towards"
_CLOSING_LINE = re.compile(
    rf"^\s*(?:{_KEYWORDS})\s+({_ISSUE}(?:\s*,\s*{_ISSUE})*)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
TITLE_HELP = "Title must be '<type>(<area>): <summary> (#<n>[, #<m>])'."
CLOSING_HELP = (
    "The description needs a closing block: e.g. 'Closes #<n>' or 'Part of #<n>'."
)


def _title_problems(match, known_areas):
    found = []
    if match["type"] not in TYPES:
        found.append("Title type must be feat, fix or improve.")
    area = match["area"]
    if area not in known_areas:
        close = difflib.get_close_matches(area, sorted(known_areas), n=1)
        hint = f" Did you mean '{close[0]}'?" if close else ""
        folders = ", ".join(f"{d}/spec" for d in DOMAINS)
        found.append(
            f"Unknown area '{area}'.{hint} Areas are the spec files in {folders}."
        )
    return found


def problems(title, body, known_areas):
    """Return what's wrong with a pull request's title and description."""
    found = []
    match = _TITLE.match(title or "")
    if match:
        found += _title_problems(match, known_areas)
    else:
        found.append(TITLE_HELP)
    text = _COMMENT.sub("", body or "")
    closing = set()
    for line in _CLOSING_LINE.findall(text):
        closing.update(re.findall(_ISSUE, line))
    if not closing:
        found.append(CLOSING_HELP)
    elif match:
        for issue in re.findall(_ISSUE, match["issues"]):
            if issue not in closing:
                found.append(f"{issue} is in the title but not in the closing block.")
    return found


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
        pull = json.load(handle).get("pull_request")
    if pull is None:
        print("No pull request in this event; nothing to check.")
        return 0
    registry = set().union(*areas(Path.cwd()).values())
    found = problems(pull.get("title"), pull.get("body"), registry)
    for problem in found:
        print(f"::error title=pr-gate::{problem}")
    if not found:
        print("Title and closing block follow contributing/spec/pull-requests.md.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
