# Implements: reports/one-page
"""A shareable HTML report for any folder of runs.

`build_report(folder)` returns the page; `write_report` saves it. The page
is built from run files alone (`games.py`), with the summary table from
`collusion_lab.summary`, a chart per group (`chart.py`), the highlight rules
(`highlights.py`) and the layout (`page.py`).
"""

from pathlib import Path

from collusion_lab.report.games import load_game, load_games
from collusion_lab.report.page import build_report

__all__ = ["build_report", "load_game", "load_games", "write_report"]


def write_report(folder, out=None, **extras):
    """Write the report (by default `report.html` in the folder); return its
    path. `extras` are `build_report`'s summary and highlights."""
    out = Path(out) if out else Path(folder) / "report.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_report(folder, **extras))
    return out
