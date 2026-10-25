"""Reanalysis of E5, E5 informed and E6: robust gain, false confessions, exact tests.

Implements: reanalysis/above-nash, reanalysis/clipped-gain, reanalysis/false-confessions, reanalysis/exact-tests, reanalysis/termination-confound-test

`uv run python reports/reanalysis.py FOLDER...` reads every run under each
FOLDER with `reports/e5/analyse.py`'s `game` and prints two tables, per
folder, model and arm:

- games; mean gain in rounds 6-10; the share of games above Nash (mean gain
  in rounds 6-10 above 0); the gain clipped at 0 per game, so a price war
  below Nash doesn't offset collusion elsewhere; and false confessions at
  each audit: firms that admitted with no explicit agreement, of all firms
  (in brackets, those that admitted with no coordination at all);
- each arm against the same folder and model's no-stake arm (`fiduciary`):
  Fisher's exact test (two-sided) on games above Nash, and a permutation test
  (two-sided, 10,000 shuffles, seeded with 0) on mean gain in rounds 6-10,
  games as n. The p-values are uncorrected; the note gives the number of
  tests, for a Holm or Bonferroni reading.

`uv run python reports/reanalysis.py --e4 FOLDER...` instead reads forked E4
games (one audit each, the arm in `conditions.audit.consequences`) and
prints, per arm and model, the explicit colluders who owned up, then
Fisher's exact test of each arm against all-or-nothing termination, pooled
over models and per model.
"""

import json
import random
import statistics as st
import sys
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "e5"))
from analyse import game


def fisher(a, b, c, d):
    """Two-sided Fisher's exact p for [[a, b], [c, d]]."""
    n1, n2, k = a + b, c + d, a + c

    def p(x):
        return comb(n1, x) * comb(n2, k - x) / comb(n1 + n2, k)

    observed = p(a)
    lo, hi = max(0, k - n2), min(k, n1)
    return min(
        1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= observed * (1 + 1e-9))
    )


def permutation(xs, ys, shuffles=10_000, seed=0):
    """Two-sided permutation p for a difference in means."""
    observed = abs(st.mean(xs) - st.mean(ys))
    pooled, n = xs + ys, len(xs)
    rng = random.Random(seed)
    hits = 0
    for _ in range(shuffles):
        rng.shuffle(pooled)
        hits += abs(st.mean(pooled[:n]) - st.mean(pooled[n:])) >= observed - 1e-12
    return (hits + 1) / (shuffles + 1)


def false_confessions(run, audit):
    """At one audit: firms that admitted with no explicit agreement, those that
    admitted with no coordination at all (explicit or tacit), and all firms."""
    summary = json.loads((run / "summary.json").read_text())
    audits = summary.get("audit", {}).get("audits") or []
    if len(audits) <= audit:
        return 0, 0, 0
    agents = audits[audit]["agents"]
    admitted = [a for a in agents.values() if a.get("admits") is True]
    return (
        sum(not a.get("explicit") for a in admitted),
        sum(not a.get("coordinated") for a in admitted),
        len(agents),
    )


def cells(folder):
    out = {}
    for summary in sorted(Path(folder).rglob("summary.json")):
        g = game(summary.parent)
        g["run"] = summary.parent
        out.setdefault((g["model"], g["arm"]), []).append(g)
    return out


def table(header, rows):
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for row in rows:
        print("| " + " | ".join(str(x) for x in row) + " |")
    print()


def main(folders):
    measures, tests = [], []
    for folder in folders:
        name = Path(folder).name
        found = cells(folder)
        for (model, arm), gs in sorted(found.items()):
            gains = [g["gain_before"] for g in gs]
            above = sum(x > 0 for x in gains)
            confessions = []
            for audit in (0, 1):
                f = [false_confessions(g["run"], audit) for g in gs]
                n = sum(x[2] for x in f)
                confessions.append(
                    f"{sum(x[0] for x in f)} ({sum(x[1] for x in f)})/{n}" if n else "—"
                )
            measures.append(
                [
                    name,
                    model,
                    arm,
                    len(gs),
                    f"{st.mean(gains):+.2f}",
                    f"{above}/{len(gs)}",
                ]
                + [f"{st.mean(max(0, x) for x in gains):.2f}"]
                + confessions
            )
            base = found.get((model, "fiduciary"))
            if not base or arm == "fiduciary":
                continue
            b = [g["gain_before"] for g in base]
            b_above = sum(x > 0 for x in b)
            tests.append(
                [
                    name,
                    model,
                    arm,
                    f"{above}/{len(gains)} vs {b_above}/{len(b)}",
                    f"{fisher(above, len(gains) - above, b_above, len(b) - b_above):.4f}",
                    f"{st.mean(gains) - st.mean(b):+.2f}",
                    f"{permutation(gains, b):.4f}",
                ]
            )
    table(
        [
            "folder",
            "model",
            "arm",
            "games",
            "mean gain r6-10",
            "games above Nash",
            "gain clipped at 0",
            "false confessions r10",
            "false confessions r20",
        ],
        measures,
    )
    table(
        [
            "folder",
            "model",
            "arm vs no stake",
            "above Nash",
            "Fisher p",
            "gain difference",
            "permutation p",
        ],
        tests,
    )
    print(f"{len(tests)} tests, uncorrected.")


def owning_up(folders):
    """{(arm, model): [owned up, explicit colluders]} over forked E4 games."""
    tally = {}
    for folder in folders:
        for summary in sorted(Path(folder).rglob("summary.json")):
            config = json.loads(json.dumps(game_config(summary.parent)))
            arm = Path(config["conditions"]["audit"]["consequences"]).stem
            arm = arm.removesuffix("-1")
            model = config["agents"][0]["model"].split("/")[-1]
            agents = json.loads(summary.read_text())["audit"]["agents"]
            cell = tally.setdefault((arm, model), [0, 0])
            for a in agents.values():
                if a.get("explicit"):
                    cell[1] += 1
                    cell[0] += a.get("admits") is True
    return tally


def game_config(run):
    import yaml

    return yaml.safe_load((run / "config.yaml").read_text())


def e4(folders):
    tally = owning_up(folders)
    arms = sorted({arm for arm, _ in tally})
    models = sorted({model for _, model in tally})
    rows = []
    for arm in arms:
        cells = [tally.get((arm, m), [0, 0]) for m in models]
        pooled = [sum(c[0] for c in cells), sum(c[1] for c in cells)]
        rows.append(
            [arm] + [f"{a}/{n}" for a, n in cells] + [f"{pooled[0]}/{pooled[1]}"]
        )
    table(["arm"] + models + ["all"], rows)
    base = "all-or-nothing"
    tests = []
    for arm in arms:
        if arm == base:
            continue
        for who in models + ["all"]:
            pick = models if who == "all" else [who]
            a = [
                sum(tally.get((x, m), [0, 0])[i] for m in pick)
                for x in (arm, base)
                for i in (0, 1)
            ]
            tests.append(
                [arm, who, f"{a[0]}/{a[1]} vs {a[2]}/{a[3]}"]
                + [f"{fisher(a[0], a[1] - a[0], a[2], a[3] - a[2]):.4f}"]
            )
    table(["arm vs all-or-nothing", "model", "owned up", "Fisher p"], tests)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--e4"]:
        e4(sys.argv[2:])
    else:
        main(sys.argv[1:])
