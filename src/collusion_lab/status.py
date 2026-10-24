# Implements: runs/failures-dont-stop-sweeps, runs/missing-runs-shown
"""Where each planned run of a config stands, in `<out>/<name>/status.json`.

`lab run` writes it when it starts (every planned run `pending`) and again
whenever a run finishes, fails or is skipped as already finished. Each run
keeps its state, its error when it failed, its labels and its resolved config,
so `lab summary` and `lab report` can count and group the runs that are
missing. Rerunning the same config updates the entries it plans and keeps the
rest.
"""

import json
from pathlib import Path

NAME = "status.json"
DONE = ("finished", "skipped")


class Status:
    def __init__(self, path):
        self.path = Path(path)
        self.runs = load(self.path)

    def plan(self, run, config):
        self.runs[run] = {
            "state": "pending",
            "labels": config.labels,
            "config": config.to_dict(),
        }

    def mark(self, run, state, error=None):
        self.runs[run]["state"] = state
        self.runs[run]["error"] = error
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"runs": self.runs}, indent=2) + "\n")


def load(path):
    path = Path(path)
    return json.loads(path.read_text())["runs"] if path.exists() else {}


def unfinished(folder):
    """Every planned run under a folder that hasn't finished, by run id."""
    runs = {}
    for path in sorted(Path(folder).rglob(NAME)):
        for run, entry in load(path).items():
            if entry["state"] not in DONE:
                runs[run] = entry
    return runs
