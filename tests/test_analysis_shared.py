# Implements: runs/analysis-shared, runs/fork-pointers
"""Each experiment's analysis script prints, on its committed runs, exactly
the tables it printed before it moved onto `collusion_lab.analysis`
(`tests/data/analyses.json`, written by the scripts as they were)."""

import contextlib
import io
import json
import runpy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = json.loads((ROOT / "tests" / "data" / "analyses.json").read_text())
ROBUSTNESS = sorted(
    str(p.relative_to(ROOT)) for p in (ROOT / "runs/robustness").iterdir() if p.is_dir()
)
CASES = {
    "lever-map-nashmid": ["reports/lever-map/analyse.py", "runs/lever-map-nashmid"],
    "lever-map-rule": ["reports/lever-map/analyse.py", "runs/lever-map-rule"],
    "lever-map-rule-grid": ["reports/lever-map/analyse.py", "runs/lever-map-rule-grid"],
    "lever-map-temptation": [
        "reports/lever-map/analyse.py",
        "runs/lever-map-temptation",
    ],
    "lever-map-temptation-grid": [
        "reports/lever-map/analyse.py",
        "runs/lever-map-temptation-grid",
    ],
    "model-survey": ["reports/model-survey/analyse.py"],
    "logging-outage": ["reports/logging-outage/analyse.py"],
    "e5-full": ["reports/e5/analyse.py", "runs/e5-full"],
    "e5-informed": ["reports/e5/analyse.py", "runs/e5-informed"],
    "e5-pilot": ["reports/e5/analyse.py", "runs/e5-pilot"],
    "e5-reasoning": ["reports/e5/analyse.py", "runs/e5-reasoning"],
    "e5-shares": [
        "reports/e5/shares.py",
        "runs/e5-informed",
        "runs/e5-full",
        "runs/e5-pilot",
    ],
    "e5-shares-reasoning": ["reports/e5/shares.py", "runs/e5-reasoning"],
    "robustness": ["reports/robustness/analyse.py", *ROBUSTNESS],
    "temptation-outage": [
        "reports/temptation-outage/metrics.py",
        "runs/temptation-outage",
    ],
    "e9": [
        "reports/e9/analyse.py",
        *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "runs/e9").iterdir()),
        "--test",
        "free-time",
        "record",
    ],
    "e9-lab-analyse": ["src/collusion_lab/cli.py", "analyse", "runs/e9"],
    "stoppable-collusion": [
        "reports/stoppable-collusion/metrics.py",
        "runs/stoppable-collusion",
    ],
}


def printed(script, *args):
    """What a script prints when run from the repository root with `args`."""
    out = io.StringIO()
    path = ROOT / script
    with (
        contextlib.chdir(ROOT),
        contextlib.redirect_stdout(out),
        pytest.MonkeyPatch.context() as patch,
    ):
        patch.setattr(sys, "argv", [str(path), *args])
        patch.syspath_prepend(str(path.parent))
        for name in ("analyse", "shares", "metrics"):  # sibling scripts, fresh
            sys.modules.pop(name, None)
        with contextlib.suppress(SystemExit):  # a script that exits with its code
            runpy.run_path(str(path), run_name="__main__")
    return out.getvalue()


@pytest.mark.parametrize("name", sorted(CASES))
def test_analysis_shared_scripts_print_what_they_printed(name):
    assert printed(*CASES[name]) == GOLDEN[name]


@pytest.mark.parametrize("folder", ["stakes-pilot-e2", "stakes-pilot-e2-policy"])
def test_analysis_shared_stakes_table_unchanged(folder, tmp_path):
    printed("reports/stakes/analyse.py", f"runs/{folder}", "--out", str(tmp_path))
    assert (tmp_path / "table.md").read_text() == GOLDEN[folder]
