# Implements: runs/summary-table
"""One table for a folder of runs, grouped by swept values or any config value.

`summarize` reads every `summary.json` under a folder (and the `manifest.json`
beside it for cost and config). Rows group runs by the swept values (their
labels) unless `by` names other keys: a label, or any config path such as
`market.rounds` or `agents.*.model` (`*` joins every agent's value). Each row
gives the number of runs, the mean market price and gain over their last
rounds, total fallbacks and total cost. List and mapping values (`seeds`)
group and print as JSON. `format_table` prints it as Markdown,
which reads in a terminal and renders in a pull request comment.
"""

import json
from pathlib import Path
from statistics import mean


def summarize(folder, by=None):
    runs = [_load(path) for path in sorted(Path(folder).rglob("summary.json"))]
    if by is None:
        by = list(dict.fromkeys(k for s, _ in runs for k in s.get("labels", {})))
    groups = {}
    for summary, manifest in runs:
        key = tuple(_value(summary, manifest, name) for name in by)
        groups.setdefault(key, []).append((summary, manifest))
    return [_row(by, key, groups[key]) for key in sorted(groups, key=_sort_key)]


def format_table(rows):
    if not rows:
        return "No runs found."
    columns = list(rows[0])
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    lines += ["| " + " | ".join(_cell(r[c]) for c in columns) + " |" for r in rows]
    return "\n".join(lines)


def _load(path):
    summary = json.loads(path.read_text())
    manifest_path = path.with_name("manifest.json")
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    return summary, manifest


def _row(by, key, runs):
    summaries = [s for s, _ in runs]
    return {
        **dict(zip(by, key, strict=True)),
        "runs": len(runs),
        "mean price": round(mean(s["market_mean_price"] for s in summaries), 2),
        "gain": round(mean(s["market_gain"] for s in summaries), 3),
        "fallbacks": sum(s["fallbacks"] for s in summaries),
        "cost": round(sum(m.get("cost") or 0 for _, m in runs), 4),
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


def _cell(value):
    return "—" if value is None else str(value)
