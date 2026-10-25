# Implements: research/findings-note
"""The findings-note draft, on a small mock sweep with one indexed moment."""

import importlib.util
from pathlib import Path

import pytest
import yaml

from collusion_lab.runner import run_config
from collusion_lab.summary import format_table, summarize

SCRIPT = Path("reports/note.py")
SWEEP = """
name: demo
seeds: [0, 1]
market: {rounds: 6, talk: true}
summary: {last_rounds: 3}
agents:
  - {id: A, model: mock/nash}
  - {id: B, model: mock/nash}
sweep:
  agents.*.model: [mock/nash, mock/proposer]
"""
SPEC = """# Demo

- **who-proposes:** Which firms propose a price first.
- **who-holds:** Whether proposals hold.

## Where this is enforced
"""


def load_script():
    spec = importlib.util.spec_from_file_location("findings_note", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def demo(make_config, tmp_path):
    """A played sweep, an experiment spec and a moments index naming one turn."""
    run_dirs = run_config(make_config(SWEEP), tmp_path / "runs")
    proposer = next(d for d in run_dirs if "proposer" in str(d))
    moments = [
        {
            "label": "opening-offer",
            "model": "mock/proposer",
            "run": str(proposer),
            "round": 1,
            "phase": "talk",
            "firm": "A",
            "field": "message",
            "quote": "Let's both charge 9.",
        },
        {
            "label": "elsewhere",
            "model": "mock/nash",
            "run": str(tmp_path / "other" / "seed-0"),
            "round": 1,
            "phase": "talk",
            "firm": "A",
            "field": "message",
            "quote": "Not in this experiment.",
        },
    ]
    (tmp_path / "moments.yaml").write_text(yaml.safe_dump(moments))
    (tmp_path / "demo.md").write_text(SPEC)
    return tmp_path


def draft(demo):
    return load_script().draft(
        demo / "runs" / "demo",
        moments=demo / "moments.yaml",
        spec=demo / "demo.md",
    )


def test_findings_note_has_the_table_highlights_and_moments(demo):
    text = draft(demo)
    assert text.startswith("<!-- Implements: demo/who-proposes, demo/who-holds -->")
    assert "# demo: findings (draft" in text
    assert format_table(summarize(demo / "runs" / "demo")) in text
    highlights = text[text.index("## Top highlights") : text.index("## Eval")]
    assert "proposes 9" in highlights
    moments = text[text.index("## Moments") :]
    assert "opening-offer" in moments and "Let's both charge 9." in moments
    assert "Not in this experiment." not in text
    assert "Eval-awareness" in text and "not counted" in text


def test_findings_note_leaves_the_researchers_parts_as_prompts(demo):
    text = draft(demo)
    for heading in ("## Short answer", "## Question and budget", "## What it can't"):
        section = text[text.index(heading) :].split("\n## ", 1)[0]
        assert "_To write:" in section, heading
    assert "4 runs" in text and "cost $0.0000" in text


def test_findings_note_writes_once_and_never_overwrites_edits(demo, capsys):
    script = load_script()
    out = demo / "reports" / "demo" / "findings.md"
    args = [
        str(demo / "runs" / "demo"),
        "--out",
        str(out),
        "--moments",
        str(demo / "moments.yaml"),
        "--spec",
        str(demo / "demo.md"),
    ]
    assert script.main(args) == 0
    assert out.read_text().startswith("<!-- Implements:")
    out.write_text("edited by the Researcher")
    assert script.main(args) == 1
    assert out.read_text() == "edited by the Researcher"
    assert "--force" in capsys.readouterr().out
    assert script.main([*args, "--force"]) == 0
    assert "## Moments" in out.read_text()
