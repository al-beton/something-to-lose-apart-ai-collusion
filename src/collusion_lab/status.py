# Implements: runs/failures-dont-stop-sweeps, runs/missing-runs-shown, runs/status-file, runs/status-command
"""Where each planned run of a config stands, in `<out>/<name>/status.json`.

`lab run` writes it when it starts (every planned run `pending`) and again
whenever a run starts (`running`), finishes, fails or is skipped as already
finished, so another process can follow a sweep by reading it. Each run keeps
its state, when it started and ended, its error when it failed, its labels and
its resolved config, so `lab summary` and `lab report` can count and group the
runs that are missing and `lab status` can list them all. Rerunning the same
config updates the entries it plans and keeps the rest. A run left `running`
or `pending` by a process that was killed stays that way until it is rerun.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

NAME = "status.json"
DONE = ("finished", "skipped")
STATES = ("pending", "running", "finished", "skipped", "failed")


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
        entry = self.runs[run]
        entry["state"] = state
        entry["error"] = error
        now = datetime.now(UTC).isoformat(timespec="seconds")
        if state == "running":
            entry["started"] = now
        elif state in ("finished", "failed"):
            entry["finished"] = now
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"runs": self.runs}, indent=2) + "\n")


def load(path):
    path = Path(path)
    return json.loads(path.read_text())["runs"] if path.exists() else {}


def every_run(folder):
    """Every planned run under a folder, by its path relative to the folder:
    run ids repeat across output folders."""
    folder = Path(folder)
    runs = {}
    for path in sorted(folder.rglob(NAME)):
        out = path.parent.parent  # status.json sits in <out>/<name>/
        for run, entry in load(path).items():
            runs[(out / run).relative_to(folder).as_posix()] = entry
    return runs


def rows(folder):
    """One row per planned run, for `lab status`: failures first, then by state."""
    runs = sorted(
        every_run(folder).items(),
        key=lambda item: (-STATES.index(item[1]["state"]), item[0]),
    )
    return [
        {
            "run": run,
            "state": entry["state"],
            "started": entry.get("started"),
            "finished": entry.get("finished"),
            "error": entry.get("error"),
        }
        for run, entry in runs
    ]


def counts(folder):
    """How many runs are in each state, as "2 finished, 1 failed"."""
    states = [entry["state"] for entry in every_run(folder).values()]
    return ", ".join(f"{states.count(s)} {s}" for s in STATES if s in states)


def unfinished(folder):
    """Every planned run under a folder that hasn't finished, keyed as in
    `every_run`."""
    return {run: e for run, e in every_run(folder).items() if e["state"] not in DONE}
