# Implements: reports/paper-rules
"""Warn when the paper breaks the sprint's limits: an abstract of 150–250
words, and at most 8 pages before References (references and appendices
don't count). The page count is read from the LaTeX .aux, so it's known
only after `make paper-pdf`. Warnings never fail the build.

Usage: python paper/check.py paper/paper.md [paper/build/paper.aux]
"""

import re
import sys
from pathlib import Path

import yaml

ABSTRACT_WORDS = (150, 250)
MAX_PAGES = 8
REFERENCES = re.compile(r"\\newlabel\{references\}\{\{[^}]*\}\{(\d+)\}")


def warnings(paper, aux=None):
    found = []
    text = Path(paper).read_text()
    front = re.match(r"(?:\s*<!--.*?-->)*\s*---\n(.*?)\n---\n", text, re.DOTALL)
    meta = (yaml.safe_load(front.group(1)) if front else None) or {}
    abstract = str(meta.get("abstract") or "")
    words = len(abstract.split())
    low, high = ABSTRACT_WORDS
    if not low <= words <= high:
        found.append(f"abstract is {words} words; the sprint asks for {low}–{high}")
    if aux and Path(aux).exists():
        match = REFERENCES.search(Path(aux).read_text())
        if match and int(match.group(1)) - 1 > MAX_PAGES:
            pages = int(match.group(1)) - 1
            found.append(
                f"{pages} pages before References; the sprint's cap is {MAX_PAGES}"
            )
    return found


if __name__ == "__main__":
    for line in warnings(*sys.argv[1:3]):
        print(f"warning: {line}")
