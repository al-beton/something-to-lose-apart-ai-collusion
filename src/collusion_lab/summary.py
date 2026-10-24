# Implements: runs/summary-table, runs/per-firm-summary, reports/summary
"""One table for a folder of runs, grouped by swept values or any config value.

`summarize` reads every `summary.json` under a folder (and the `manifest.json`
beside it for cost and config). Rows group runs by the swept values (their
labels) unless `by` names other keys: a label, or any config path such as
`market.rounds` or `agents.*.model` (`*` joins every agent's value). Each row
gives the number of runs, the mean market price and gain over their last
rounds, total fallbacks and total cost, then which firms a script (a `mock/`
model) played, and each firm's own mean price, gain, fallbacks and cost
(from its turn and timing logs). When a run has both scripted and model
firms, its headline mean price and gain are the model firms' alone. List and mapping values (`seeds`)
group and print as JSON. `format_table` prints it as Markdown,
which reads in a terminal and renders in a pull request comment.

`group_runs` is the grouping on its own, for anything else that shows a
folder group by group (reports).
"""

import json
from pathlib import Path
from statistics import mean
from typing import NamedTuple

from collusion_lab.backends import is_mock

FIRM_COLUMNS = ("price", "gain", "fallbacks", "cost")


class Run(NamedTuple):
    dir: Path
    summary: dict
    manifest: dict


def group_runs(folder, by=None):
    """The keys grouped by, and (key, runs) pairs in table order."""
    runs = [_load(path) for path in sorted(Path(folder).rglob("summary.json"))]
    if by is None:
        by = list(dict.fromkeys(k for r in runs for k in r.summary.get("labels", {})))
    groups = {}
    for run in runs:
        key = tuple(_value(run.summary, run.manifest, name) for name in by)
        groups.setdefault(key, []).append(run)
    return by, [(key, groups[key]) for key in sorted(groups, key=_sort_key)]


def summarize(folder, by=None):
    by, groups = group_runs(folder, by)
    firms = list(
        dict.fromkeys(f for _, runs in groups for r in runs for f in _firms(r))
    )
    return [_row(by, key, runs) | _firm_columns(firms, runs) for key, runs in groups]


def format_table(rows):
    if not rows:
        return "No runs found."
    columns = list(rows[0])
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    lines += ["| " + " | ".join(cell(r[c]) for c in columns) + " |" for r in rows]
    return "\n".join(lines)


def _load(path):
    summary = json.loads(path.read_text())
    manifest_path = path.with_name("manifest.json")
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    return Run(path.parent, summary, manifest)


def _row(by, key, runs):
    summaries = [r.summary for r in runs]
    headlines = [_headline(r) for r in runs]
    scripted = sorted({f for r in runs for f in _scripted(r)})
    return {
        **dict(zip(by, key, strict=True)),
        "runs": len(runs),
        "mean price": round(mean(price for price, _ in headlines), 2),
        "gain": round(mean(gain for _, gain in headlines), 3),
        "fallbacks": sum(s["fallbacks"] for s in summaries),
        "cost": round(sum(r.manifest.get("cost") or 0 for r in runs), 4),
        "scripted": ", ".join(scripted) or None,
    }


def _firms(run):
    return list(run.summary.get("mean_price", {}))


def _scripted(run):
    agents = run.manifest.get("config", {}).get("agents", [])
    return {a["id"] for a in agents if is_mock(a["model"])}


def _headline(run):
    """The run's mean price and gain: the model firms' when a script plays too."""
    s = run.summary
    models = [f for f in _firms(run) if f not in _scripted(run)]
    if not models or len(models) == len(_firms(run)):
        return s["market_mean_price"], s["market_gain"]
    return mean(s["mean_price"][f] for f in models), mean(s["gain"][f] for f in models)


def _firm_columns(firms, runs):
    """Each firm's own mean price, gain, fallbacks and cost over these runs."""
    columns = {}
    for firm in firms:
        played = [r for r in runs if firm in _firms(r)]
        if not played:
            columns |= dict.fromkeys(f"{firm} {c}" for c in FIRM_COLUMNS)
            continue
        turns = [t for r in played for t in _lines(r.dir / "turns.jsonl")]
        calls = [t for r in played for t in _lines(r.dir / "timings.jsonl")]
        columns |= {
            f"{firm} price": round(
                mean(r.summary["mean_price"][firm] for r in played), 2
            ),
            f"{firm} gain": round(mean(r.summary["gain"][firm] for r in played), 3),
            f"{firm} fallbacks": sum(
                1 for t in turns if t["agent"] == firm and t["error"]
            ),
            f"{firm} cost": round(
                sum(c.get("cost") or 0 for c in calls if c["agent"] == firm), 4
            ),
        }
    return columns


def _lines(path):
    if not path.exists():
        return []
    with path.open() as log:
        return [json.loads(line) for line in log if line.strip()]


def _value(summary, manifest, name):
    if name in summary.get("labels", {}):
        value = summary["labels"][name]
    else:
        value = _lookup(manifest.get("config", {}), name.split("."))
    # Lists and mappings group by their JSON text, which also reads well.
    return json.dumps(value) if isinstance(value, list | dict) else value


def _lookup(node, keys):
    for i, key in enumerate(keys):
        if key == "*" and isinstance(node, list):
            values = [_lookup(item, keys[i + 1 :]) for item in node]
            return ",".join(str(v) for v in values)
        if isinstance(node, list) and key.isdigit() and int(key) < len(node):
            node = node[int(key)]
        elif isinstance(node, dict) and key in node:
            node = node[key]
        else:
            return None
    return node


def _sort_key(key):
    return tuple(
        (0, v, "") if isinstance(v, int | float) else (1, 0, str(v)) for v in key
    )


def cell(value):
    """How a table shows one value."""
    return "—" if value is None else str(value)
