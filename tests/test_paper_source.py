# Implements: reports/paper-source
"""The paper's Markdown source builds to LaTeX (skipped where pandoc isn't installed, as in CI)."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = (
    "Introduction",
    "Related Work",
    "Methods",
    "Results",
    "Discussion and Limitations",
    "Limitations",
    "Future Work",
    "Conclusion",
    "Code and Data",
    "References",
)


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc isn't installed")
def test_paper_source_builds_to_latex_with_title_and_sections(tmp_path):
    out = tmp_path / "paper.tex"
    subprocess.run(
        ["make", "-s", "paper-tex", f"PAPER_BUILD={tmp_path}"], cwd=ROOT, check=True
    )
    tex = out.read_text()
    assert r"\documentclass" in tex and r"\end{document}" in tex
    assert r"\hackathonbox" in tex and r"\tableofcontents" in tex
    title = (ROOT / "paper" / "paper.md").read_text().split("title:", 1)[1]
    assert title.splitlines()[0].strip().strip("\"'") in tex
    for name in SECTIONS:
        assert f"{{{name}}}" in tex, name
    assert r"\appendix" in tex
