# Implements: runs/summary-table, runs/missing-runs-shown, runs/fallback-rates, reports/summary
"""One table for a folder of runs, grouped by swept values or any config value.

`summarize` reads every `summary.json` under a folder (and the `manifest.json`
beside it for cost and config). Rows group runs by the swept values (their
labels) unless `by` names other keys: a label, or any config path such as
`market.rounds` or `agents.*.model` (`*` joins every agent's value). Each row
gives the number of runs, the mean market price and gain over their last
rounds, total fallbacks and total cost, and how many of its planned runs are
`missing` (failed or never finished, from `status.json`; see status.py), which
the means leave out. List and mapping values (`seeds`)
group and print as JSON. `format_table` prints it as Markdown,
which reads in a terminal and renders in a pull request comment.

`reply_rates` gives, per model, its turns, unreadable replies, fallbacks,
fallback rate and the reasons; `flagged_runs` names every run where more than
`FLAG_RATE` of all turns fell back. Runs written before replies were counted
contribute nothing to either.

`group_runs` is the grouping on its own, for anything else that shows a
folder group by group (reports).
"""

import json
from pathlib import Path
from statistics import mean
from typing import NamedTuple

from collusion_lab.status import unfinished

FLAG_RATE = 0.1  # flag a run when more than one turn in ten fell back


class Run(NamedTuple):
    dir: Path
    summary: dict | None  # None for a run that's missing
    manifest: dict

    @property
    def labels(self):
        if self.summary:
            return self.summary.get("labels", {})
        return self.manifest.get("config", {}).get("labels", {})


def group_runs(folder, by=None):
    """The keys grouped by, and (key, runs) pairs in table order; a group's
    missing runs come with `summary` None."""
    runs = _finished(folder)
    runs += [
        Run(Path(folder), None, {"config": entry["config"]})
        for entry in unfinished(folder).values()
    ]
    if by is None:
        by = list(dict.fromkeys(k for r in runs for k in r.labels))
    groups = {}
    for run in runs:
        key = tuple(_value(run, name) for name in by)
        groups.setdefault(key, []).append(run)
    return by, [(key, groups[key]) for key in sorted(groups, key=_sort_key)]


def summarize(folder, by=None):
    by, groups = group_runs(folder, by)
    return [_row(by, key, runs) for key, runs in groups]


def _finished(folder):
    return [_load(path) for path in sorted(Path(folder).rglob("summary.json"))]


def _reasons(counts):
    return ", ".join(
        f"{k} {n}" for k, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    )


def reply_rates(folder):
    """One row per model: how its replies went, over every run in the folder."""
    totals = {}
    for run in _finished(folder):
        for model, row in run.summary.get("replies", {}).items():
            total = totals.setdefault(
                model, {"turns": 0, "unreadable": 0, "fallbacks": 0, "reasons": {}}
            )
            for field in ("turns", "unreadable", "fallbacks"):
                total[field] += row[field]
            for reason, n in row["reasons"].items():
                total["reasons"][reason] = total["reasons"].get(reason, 0) + n
    return [
        {
            "model": model,
            "turns": t["turns"],
            "unreadable": t["unreadable"],
            "fallbacks": t["fallbacks"],
            "fallback rate": round(t["fallbacks"] / t["turns"], 3),
            "reasons": _reasons(t["reasons"]),
        }
        for model, t in sorted(totals.items())
    ]


def flagged_runs(folder):
    """Every run in which more than FLAG_RATE of its turns fell back."""
    flagged = []
    for run in _finished(folder):
        rows = run.summary.get("replies", {}).values()
        turns = sum(r["turns"] for r in rows)
        fallbacks = sum(r["fallbacks"] for r in rows)
        if turns and fallbacks / turns > FLAG_RATE:
            reasons = {}
            for r in rows:
                for reason, n in r["reasons"].items():
                    reasons[reason] = reasons.get(reason, 0) + n
            flagged.append(
                {
                    "run": run.summary["run"],
                    "fallback rate": round(fallbacks / turns, 3),
                    "reasons": _reasons(reasons),
                }
            )
    return flagged


def format_replies(folder):
    """The per-model reply table and flagged runs, or "" when every reply
    could be read."""
    rates = reply_rates(folder)
    if not any(r["unreadable"] for r in rates):
        return ""
    lines = ["Replies by model:", "", format_table(rates)]
    for flag in flagged_runs(folder):
        lines.append(
            f"Flagged: {flag['run']} ({flag['fallback rate']:.0%} of turns fell "
            f"back: {flag['reasons']})"
        )
    return "\n".join(lines)


def missing_runs(folder):
    """Each run planned under a folder that failed or never finished."""
    return [
        {"run": run, "state": entry["state"], "error": entry.get("error")}
        for run, entry in unfinished(folder).items()
    ]


def format_missing(folder):
    """One line per missing run, or "" when none is."""
    return "\n".join(
        f"Missing: {m['run']} ({m['state']}){': ' + m['error'] if m['error'] else ''}"
        for m in missing_runs(folder)
    )


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
    summaries = [r.summary for r in runs if r.summary]

    def average(field, digits):
        values = [s[field] for s in summaries]
        return round(mean(values), digits) if values else None

    return {
        **dict(zip(by, key, strict=True)),
        "runs": len(summaries),
        "missing": len(runs) - len(summaries),
        "mean price": average("market_mean_price", 2),
        "gain": average("market_gain", 3),
        "fallbacks": sum(s["fallbacks"] for s in summaries),
        "cost": round(sum(r.manifest.get("cost") or 0 for r in runs), 4),
    }


def _value(run, name):
    if name in run.labels:
        value = run.labels[name]
    else:
        value = _lookup(run.manifest.get("config", {}), name.split("."))
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
