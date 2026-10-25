# Implements: reports/paper-figures
"""The paper build, end to end on the committed runs: offline, a few seconds."""

import importlib.util
from pathlib import Path

SCRIPT = Path("reports/paper/build.py")
FIGURES = (
    "prices-stoppable",
    "prices-e2",
    "disclosure",
    "collusion-vs-disclosure",
    "ladder",
)


def load():
    spec = importlib.util.spec_from_file_location("paper_build", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paper_figures_from_committed_runs(tmp_path):
    assert load().main(["--out", str(tmp_path)]) == 0
    for name in FIGURES:
        assert (tmp_path / f"{name}.png").read_bytes()[:4] == b"\x89PNG"
        svg = (tmp_path / f"{name}.svg").read_text()
        assert "<svg" in svg and "#ffffff" in svg.lower()  # light background
    ladder = (tmp_path / "ladder.md").read_text()
    assert "| arm |" in ladder and "baseline" in ladder and "10/10" in ladder
    e2 = (tmp_path / "e2.md").read_text()
    assert "honest disclosure" in e2 and "termination" in e2


def test_paper_figures_show_nash_and_joint_prices(tmp_path):
    load().main(["--out", str(tmp_path)])
    svg = (tmp_path / "prices-stoppable.svg").read_text()
    assert "Nash 8" in svg and "joint 45" in svg
