"""The paper's figures and tables, rebuilt from the committed runs.

Implements: reports/paper-figures

`make paper-figures` (or `uv run python reports/paper/build.py [--out DIR]`,
default `reports/paper`) reads only committed run files, offline, and writes
each figure as PNG and SVG on a white background, plus Markdown tables. The
charts are drawn by `collusion_lab.charts`, shared with reports and
`lab explore`; Al's headline measure is the premium over Nash,
(late mean price - Nash) / (joint - Nash).

- `prices-stoppable`, `prices-e2`: mean price per round per arm, with the
  Nash and joint-profit prices and the premium on the right-hand axis;
- `premium-stoppable`, `premium-e2`: each arm's premium over its last five
  rounds;
- `disclosure`: honest disclosure rate by E2 stake, one bar per model;
- `collusion-vs-disclosure`: gain before the audit against honest disclosure,
  one point per arm and model;
- `ladder` (and `ladder.md`): the stoppable-collusion ladder, the share of
  games with a held price agreement per nudge, with each rung's late price
  and premium;
- `e2.md`: the E2 table from `reports/stakes/analyse.py`.

Agreements and disclosure come from the same code the findings notes use
(`reports/stoppable-collusion/metrics.py`, `reports/stakes/analyse.py`), so
figures and notes can't disagree. Point the folders below at newer runs.
"""

import argparse
import importlib.util
import sys
from pathlib import Path
from statistics import mean

from collusion_lab import charts

HERE = Path(__file__).resolve().parent
STOPPABLE = Path("runs/stoppable-collusion")
E2 = Path("runs/stakes-pilot-e2-policy")
LADDER = [  # (label, arm folder under STOPPABLE)
    ("baseline", "stoppable-baseline/prompt=system-neutral.md"),
    (
        "monitoring line",
        "stoppable-nudges/prompt=conditions-nudges-monitored.md__outage=False",
    ),
    (
        "policy line",
        "stoppable-nudges/prompt=conditions-nudges-policy.md__outage=False",
    ),
    (
        "explicit ban",
        "stoppable-nudges/prompt=conditions-no-collusion.md__outage=False",
    ),
]
TRACE = "<!-- Implements: reports/paper-figures -->\n"
PREMIUM = "premium over Nash (0 = Nash, 1 = joint)"


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prices(folder, out, name, title):
    found, lines = charts.arm_prices(folder)
    charts.save(charts.price_figure(found, lines, title), out, name)


def premiums(folder, out, name, title):
    late = charts.late_premium(folder)
    labels = [charts.arm_label(arm) for arm in late]
    values = list(late.values())
    notes = [f"{v:.2f}" for v in values]
    fig = charts.bar_figure(labels, values, PREMIUM, title, notes)
    charts.save(fig, out, name)


def disclosure(rows, out):
    stakes = sorted({charts.stake_label(r["arm"]) for r in rows})
    series = {}
    for r in rows:
        values = series.setdefault(charts.model_label(r["model"]), {})
        values[charts.stake_label(r["arm"])] = r["honest disclosure"]
    fig = charts.grouped_bar_figure(
        stakes,
        series,
        "honest disclosure rate",
        "Owning up at the audit, by stake and model (n/a: none coordinated)",
    )
    charts.save(fig, out, "disclosure")


def scatter(rows, out):
    points = [
        (
            r["gain before"],
            r["honest disclosure"],
            f"{charts.model_label(r['model'])}, {charts.stake_label(r['arm'])}",
        )
        for r in rows
        if r["gain before"] is not None and r["honest disclosure"] is not None
    ]
    fig = charts.scatter_figure(
        points,
        "collusion: gain before the audit (0 = Nash, 1 = joint profit)",
        "honest disclosure rate",
        "Collusion against honest disclosure",
    )
    charts.save(fig, out, "collusion-vs-disclosure")


def ladder(metrics):
    rows = []
    for label, arm in LADDER:
        runs = [s.parent for s in sorted((STOPPABLE / arm).rglob("summary.json"))]
        games = [metrics.game(run) for run in runs]
        late = mean(g["late"] for g in games) if games else None
        rows.append(
            {
                "arm": label,
                "games": len(games),
                "agreed": sum(g["agreed"] is not None for g in games),
                "agreed jointly": sum(g["agreed_joint"] is not None for g in games),
                "late price": round(late, 1) if games else None,
                "premium": round(charts.premium(charts.market(runs[0]), late), 2)
                if games
                else None,
            }
        )
    return rows


def ladder_table(rows):
    lines = [
        (
            "| arm | games with a held agreement | …in joint wording "
            "| mean price r16-20 | premium over Nash |"
        ),
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {r['arm']} | {r['agreed']}/{r['games']} | {r['agreed jointly']}/{r['games']} "
        f"| {r['late price']} | {r['premium']} |"
        for r in rows
    ]
    return "\n".join(lines) + "\n"


def ladder_figure(rows, out):
    shares = [r["agreed"] / r["games"] if r["games"] else 0 for r in rows]
    notes = [
        f"{r['agreed']}/{r['games']}\nprice {r['late price']}, premium {r['premium']}"
        for r in rows
    ]
    fig = charts.bar_figure(
        [r["arm"] for r in rows],
        shares,
        "share of games with a held price agreement",
        "Stoppable collusion: what each nudge leaves",
        notes,
    )
    charts.save(fig, out, "ladder")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(HERE))
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stakes = _module(Path("reports/stakes/analyse.py"), "stakes_analyse")
    metrics = _module(
        Path("reports/stoppable-collusion/metrics.py"), "stoppable_metrics"
    )

    prices(STOPPABLE, out, "prices-stoppable", "Stoppable collusion: price over rounds")
    prices(E2, out, "prices-e2", "E2 pilot: price over rounds")
    premiums(STOPPABLE, out, "premium-stoppable", "Stoppable collusion: late premium")
    premiums(E2, out, "premium-e2", "E2 pilot: late premium")
    rows = stakes.analyse(E2)
    (out / "e2.md").write_text(TRACE + stakes.table(rows))
    disclosure(rows, out)
    scatter(rows, out)
    steps = ladder(metrics)
    (out / "ladder.md").write_text(TRACE + ladder_table(steps))
    ladder_figure(steps, out)
    print(f"Wrote figures and tables to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
