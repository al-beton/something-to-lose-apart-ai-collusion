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
    assert "{hackathonbox}" in tex and r"\tableofcontents" in tex
    title = (ROOT / "paper" / "paper.md").read_text().split("title:", 1)[1]
    assert title.splitlines()[0].strip().strip("\"'") in tex
    for name in SECTIONS:
        assert f"{{{name}}}" in tex, name
    assert r"\appendix" in tex


def _check():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "paper_check", ROOT / "paper" / "check.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paper_rules_warn_on_abstract_length_and_page_cap(tmp_path):
    check = _check()
    paper = tmp_path / "paper.md"
    paper.write_text(
        "---\ntitle: T\nabstract: |\n  " + "word " * 120 + "\n---\n\n# Introduction\n"
    )
    assert "120 words" in " ".join(check.warnings(paper))
    paper.write_text("---\nabstract: |\n  " + "word " * 200 + "\n---\n")
    aux = tmp_path / "paper.aux"
    aux.write_text(r"\newlabel{main-end}{{}{10}{}{section*.8}{}}" + "\n")
    found = " ".join(check.warnings(paper, aux))
    assert "words" not in found and "10 pages" in found
    aux.write_text(r"\newlabel{main-end}{{}{8}{}{section*.8}{}}" + "\n")
    assert check.warnings(paper, aux) == []


def test_paper_rules_skeleton_carries_the_sprint_requirements():
    text = (ROOT / "paper" / "paper.md").read_text()
    assert "# Limitations and Dual-Use / Ethical Considerations" in text
    results = text.split("# Results", 1)[1].split("\n# ", 1)[0]
    for word in ("variance", "seeds", "baselines", "positive control"):
        assert word in results, word
    assert "\\label{main-end}" in text.split("# References", 1)[0]
    assert "written during the sprint" in text.split("# Code and Data", 1)[1]
