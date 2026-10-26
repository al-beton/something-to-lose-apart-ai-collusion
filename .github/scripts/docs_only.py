# Implements: ci/docs-fast
"""docs-only: does a pull request change only the paper's text, the submission
pack or READMEs? Then the gate skips the linter, the tests and the digest, and
keeps the title check and the spec check (contributing/spec/ci.md).

Prints `docs_only=true` or `docs_only=false`, and appends the same line to
$GITHUB_OUTPUT when it is set. Takes the base ref to diff against.
"""

import fnmatch
import os
import subprocess
import sys

DOCS = ("submission/*", "paper/*.md", "paper/*.bib", "README.md", "*/README.md")


def is_docs(path):
    """True for a file whose change can't break code, tests or numbers."""
    return any(fnmatch.fnmatch(path, pattern) for pattern in DOCS)


def docs_only(paths):
    """True when every changed path is docs (and something changed)."""
    return bool(paths) and all(is_docs(p) for p in paths)


def changed(base):
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def main():
    line = f"docs_only={str(docs_only(changed(sys.argv[1]))).lower()}"
    print(line)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(line + "\n")


if __name__ == "__main__":
    main()
