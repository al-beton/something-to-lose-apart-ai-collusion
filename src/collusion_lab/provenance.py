# Implements: reproducibility/provenance-log
"""One append-only log of every command that played or asked anything.

`lab run`, `lab explore` and `lab debrief` each append one JSON line to
`runs/index.jsonl` (or `$LAB_INDEX`): when it started and ended, the command
line, the lab's commit and whether the checkout was dirty, its spend cap, what
it spent (summed from the manifests of the runs it played; None when a fresh
call had no known price, and for a debrief, which records its `estimate`
instead), its output folder, the runs it played and the session that ran it
(`$LAB_SESSION`, which each agent session sets; None otherwise). Lines are
only ever appended.

`backfill(folder)` gives every run under a folder that isn't in the log yet
a line from its manifest, marked `backfilled`: one per run, since the
commands that made them weren't recorded.
"""

import json
import os
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path

from collusion_lab import manifest

DEFAULT_INDEX = "runs/index.jsonl"


def index_path():
    return Path(os.environ.get("LAB_INDEX", DEFAULT_INDEX))


def now():
    return datetime.now(UTC).isoformat(timespec="seconds")


def record(command, argv, out, cap, spent, runs, started=None, **extra):  # noqa: PLR0913
    """Append one command's line; `argv` is the command line as run."""
    code = manifest.code()
    _append(
        {
            "started": started or now(),
            "ended": now(),
            "command": command,
            "argv": shlex.join(["lab", *argv[1:]]) if argv else None,
            "commit": code["commit"],
            "dirty": code["dirty"],
            "cap": cap,
            "spent": spent,
            "out": str(out),
            "runs": runs,
            "session": os.environ.get("LAB_SESSION"),
            **extra,
        }
    )


def spent(run_dirs):
    """What the played runs spent, from their manifests; None if unknown."""
    costs = []
    for run_dir in run_dirs:
        path = Path(run_dir) / "manifest.json"
        if path.exists():
            costs.append(json.loads(path.read_text()).get("cost"))
    return None if None in costs else round(sum(costs), 6)


def backfill(folder):
    """A `backfilled` line for every run under `folder` not yet in the log."""
    folder = Path(folder)
    logged = set()
    if index_path().exists():
        for line in index_path().read_text().splitlines():
            entry = json.loads(line)
            logged |= {f"{entry.get('out')}/{run}" for run in entry.get("runs") or []}
    found = []
    for path in sorted(folder.rglob("manifest.json")):
        run = path.parent.relative_to(folder).as_posix()
        if f"{folder}/{run}" in logged:
            continue
        record_ = json.loads(path.read_text())
        found.append((record_.get("started") or "", run, record_))
    for started, run, record_ in sorted(found):
        code = record_.get("code") or {}
        _append(
            {
                "started": started or None,
                "ended": record_.get("finished"),
                "command": None,
                "argv": None,
                "commit": code.get("commit"),
                "dirty": code.get("dirty"),
                "cap": (record_.get("config") or {}).get("budget"),
                "spent": record_.get("cost"),
                "out": str(folder),
                "runs": [run],
                "session": None,
                "backfilled": True,
            }
        )


def _append(line):
    path = index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as index:
        index.write(json.dumps(line, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    for folder in sys.argv[1:] or ["runs"]:
        backfill(folder)
