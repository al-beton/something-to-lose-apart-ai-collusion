# Implements: runs/summary-table, reports/summary
"""One table for a folder of runs, grouped by swept values or any config value.

`summarize` reads every `summary.json` under a folder (and the `manifest.json`
beside it for cost and config). Rows group runs by the swept values (their
labels) unless `by` names other keys: a label, or any config path such as
`market.rounds` or `agents.*.model` (`*` joins every agent's value). Each row
gives the number of runs, the mean market price and gain over their last
rounds, total fallbacks and total cost. List and mapping values (`seeds`)
group and print as JSON. `format_table` prints it as Markdown,
which reads in a terminal and renders in a pull request comment.

`group_runs` is the grouping on its own, for anything else that shows a
folder group by group (reports).
"""

import json
from pathlib import Path
from statistics import mean
from typing import NamedTuple


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
    return [_row(by, key, runs) for key, runs in groups]


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
    return {
        **dict(zip(by, key, strict=True)),
        "runs": len(runs),
        "mean price": round(mean(s["market_mean_price"] for s in summaries), 2),
        "gain": round(mean(s["market_gain"] for s in summaries), 3),
        "fallbacks": sum(s["fallbacks"] for s in summaries),
        "cost": round(sum(r.manifest.get("cost") or 0 for r in runs), 4),
    }


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
