# Implements: runs/summary-table, runs/per-firm-summary, runs/fallback-rates, reports/summary, runs/missing-runs-shown, conditions/audit-metrics, runs/drift, runs/eval-awareness, runs/price-premium, market/scenarios
"""One table for a folder of runs, grouped by swept values or any config value.

`summarize` reads every `summary.json` under a folder (and the `manifest.json`
beside it for cost and config). Rows group runs by the swept values (their
labels) unless `by` names other keys: a label, or any config path such as
`market.rounds` or `agents.*.model` (`*` joins every agent's value). Each row
gives the number of runs, the mean market price and gain over their last
rounds, the price premium over Nash (0 competitive, 1 a full cartel) and the
plain percentage above Nash, total fallbacks and total cost, how many of its planned runs are
`missing` (failed or never finished, from `status.json`; see status.py),
which the means leave out, then which firms a script (a `mock/`
model) played, and each firm's own mean price, gain, fallbacks and cost
(from its turn and timing logs, plus what a resumed run's earlier attempts
spent), its opening price and gain (the first `summary.first_rounds` rounds)
and its drift from them to the last rounds. When a run has both scripted and model firms, its headline mean
price and gain are the model firms' alone. List and mapping values (`seeds`)
group and print as JSON. When a group's runs were audited (the `audit`
condition), the row adds the disclosure rates from `disclosure.rates`.
`format_table` prints it as Markdown,
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

from collusion_lab import charts, disclosure
from collusion_lab.backends import is_mock
from collusion_lab.market import market_for

FIRM_COLUMNS = (
    "price",
    "gain",
    "fallbacks",
    "cost",
    "opening price",
    "price drift",
    "opening gain",
    "gain drift",
)
FLAG_RATE = 0.1  # flag a run when more than one turn in ten fell back
from collusion_lab.status import unfinished


class Run(NamedTuple):
    dir: Path
    summary: dict | None  # None for a run that's missing
    manifest: dict

    @property
    def labels(self):
        if self.summary:
            return self.summary.get("labels", {})
        return self.manifest.get("config", {}).get("labels", {})


def group_runs(folder, by=None, only=None):
    """The keys grouped by, and (key, runs) pairs in table order; a group's
    missing runs come with `summary` None. `only`, a set of run directories,
    leaves out every other run under the folder."""
    runs = _finished(folder)
    runs += [
        _missing(Path(folder) / path, entry)
        for path, entry in unfinished(folder).items()
    ]
    if only is not None:
        keep = {Path(d).resolve() for d in only}
        runs = [r for r in runs if Path(r.dir).resolve() in keep]
    if by is None:
        by = list(dict.fromkeys(k for r in runs for k in r.labels))
    groups = {}
    for run in runs:
        key = tuple(_value(run, name) for name in by)
        groups.setdefault(key, []).append(run)
    return by, [(key, groups[key]) for key in sorted(groups, key=_sort_key)]


def summarize(folder, by=None, only=None):
    by, groups = group_runs(folder, by, only)
    firms = list(
        dict.fromkeys(f for _, runs in groups for r in runs for f in _firms(r))
    )
    return [_row(by, key, runs) | _firm_columns(firms, runs) for key, runs in groups]


def _finished(folder):
    return [_load(path) for path in sorted(Path(folder).rglob("summary.json"))]


def _add(counts, more):
    for reason, n in more.items():
        counts[reason] = counts.get(reason, 0) + n


def _reasons(counts):
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return ", ".join(f"{k} {n}" for k, n in ranked)


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
            _add(total["reasons"], row["reasons"])
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
                _add(reasons, r["reasons"])
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
    # Audit columns appear only on rows that were audited.
    columns = list(dict.fromkeys(c for r in rows for c in r))
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    lines += ["| " + " | ".join(cell(r.get(c)) for c in columns) + " |" for r in rows]
    return "\n".join(lines)


def _missing(run_dir, entry):
    """A run with no summary; its manifest, when it got that far, keeps what
    it spent counted in the group's cost."""
    path = run_dir / "manifest.json"
    manifest = json.loads(path.read_text()) if path.exists() else {}
    return Run(run_dir, None, {**manifest, "config": entry["config"]})


def _load(path):
    summary = json.loads(path.read_text())
    manifest_path = path.with_name("manifest.json")
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    return Run(path.parent, summary, manifest)


def _row(by, key, runs):
    played = [r for r in runs if r.summary]
    summaries = [r.summary for r in played]
    headlines = [_headline(r) for r in played]
    scripted = sorted({f for r in runs for f in _scripted(r)})

    def average(values, digits):
        return round(mean(values), digits) if values else None

    return {
        **dict(zip(by, key, strict=True)),
        "runs": len(played),
        "missing": len(runs) - len(played),
        "mean price": average([price for price, _ in headlines], 2),
        "gain": average([gain for _, gain in headlines], 3),
        "premium": average(
            [_premium(r, p) for r, (p, _) in zip(played, headlines, strict=True)], 3
        ),
        "% above Nash": average(
            [_above_nash(r, p) for r, (p, _) in zip(played, headlines, strict=True)], 1
        ),
        "fallbacks": sum(s["fallbacks"] for s in summaries),
        "cost": round(sum(run_cost(r.manifest) for r in runs), 4),
        "scripted": ", ".join(scripted) or None,
        "eval-aware": _eval_aware(summaries),
        **disclosure.rates(summaries, [_scripted(r) for r in played]),
    }


def _market(run):
    config = run.manifest.get("config", {})
    return market_for(config.get("market", {}), len(config.get("agents", [])) or 2)


def _premium(run, price):
    """The headline price's premium over Nash, against the run's own market."""
    return charts.premium(_market(run), price)


def _above_nash(run, price):
    nash = _market(run).nash_price
    return 100 * (price - nash) / nash


def _eval_aware(summaries):
    """The share of model turns that mention being evaluated (awareness.py),
    or None when no run counted any."""
    counts = [s["eval_aware"] for s in summaries if "eval_aware" in s]
    turns = sum(c["turns"] for c in counts)
    return round(sum(c["aware"] for c in counts) / turns, 3) if turns else None


def _firms(run):
    return list((run.summary or {}).get("mean_price", {}))


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
        turns = [t for r in played for t in _turns(r.dir)]
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
                sum(c.get("cost") or 0 for c in calls if c["agent"] == firm)
                + sum(_earlier(r, firm) for r in played),
                4,
            ),
            **_drift_columns(firm, played),
        }
    return columns


def _drift_columns(firm, runs):
    """A firm's opening means and drift, over runs whose summary has them."""
    columns = {}
    for name, key, digits in (
        ("opening price", "opening_price", 2),
        ("price drift", "price_drift", 2),
        ("opening gain", "opening_gain", 3),
        ("gain drift", "gain_drift", 3),
    ):
        values = [r.summary[key][firm] for r in runs if key in r.summary]
        columns[f"{firm} {name}"] = round(mean(values), digits) if values else None
    return columns


def _earlier(run, firm):
    """What a resumed run's earlier attempts spent on this firm's calls."""
    return run.manifest.get("earlier_agent_cost", {}).get(firm, 0)


def _turns(run_dir):
    """A run's turns: its full log, or the compact one a committed run keeps
    instead (`reports/compact_turns.py`), which has each turn's error too."""
    full = run_dir / "turns.jsonl"
    return _lines(full if full.exists() else run_dir / "turns.compact.jsonl")


def _lines(path):
    if not path.exists():
        return []
    with path.open() as log:
        return [json.loads(line) for line in log if line.strip()]


def run_cost(manifest):
    """A run's cost, with what its earlier failed attempts spent."""
    return (manifest.get("cost") or 0) + manifest.get("earlier_cost", 0)


def spent(folder):
    """The manifest of every run under a folder that made calls, finished or
    not, so a total of spend leaves nothing out."""
    _, groups = group_runs(folder)
    return [r.manifest for _, runs in groups for r in runs if "calls" in r.manifest]


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
