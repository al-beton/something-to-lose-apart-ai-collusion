"""Rescore the audit block of committed audited runs with the current rule.

Implements: research/every-run-committed

`uv run python reports/stakes/rescore.py FOLDER [--check]` finds every run
under FOLDER whose `summary.json` has an `audit` block, rebuilds that block
from the run's `config.yaml` and `turns.compact.jsonl` with the audit
condition's own `summary` (who coordinated explicitly or tacitly, who agreed
at any price, what each firm answered), and writes it back. Nothing else in
the summary changes. With `--check` it writes nothing and exits 1 if any
run's stored block differs from the rescored one, so a folder can be shown
to be scored by the current rule.
"""

import json
import sys
from pathlib import Path

from collusion_lab.config import load_config
from collusion_lab.market import Bertrand


def rescored(run):
    config = load_config(run / "config.yaml")
    m = config.market
    market = Bertrand(m.a, m.b, m.c, m.price_min, m.price_max)
    models = {a.id: a.model for a in config.agents}
    turns = [
        {**t, "model": models[t["agent"]]}
        for t in map(json.loads, (run / "turns.compact.jsonl").open())
    ]
    return config.conditions["audit"].summary(turns, market)


def main(folder, check=False):
    stale = []
    for path in sorted(Path(folder).rglob("summary.json")):
        summary = json.loads(path.read_text())
        if "audit" not in summary:
            continue
        audit = rescored(path.parent)
        if audit != summary["audit"]:
            stale.append(path.parent)
            if not check:
                summary["audit"] = audit
                path.write_text(json.dumps(summary, indent=2) + "\n")
    for run in stale:
        print(f"{'stale' if check else 'rescored'}: {run}")
    return 1 if check and stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--check" in sys.argv[2:]))
