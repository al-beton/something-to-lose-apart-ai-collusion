# Implements: e9-crux/question, e9-crux/no-stake-stays-silent, e9-crux/ceiling, e9-crux/stake-defects, e9-crux/review-dose, e9-crux/firm-cost-dose, e9-crux/freedom-equals-self, e9-crux/ownership, e9-crux/not-eagerness, e9-crux/across-models, e9-crux/came-forward, e9-crux/false-confessions, e9-crux/tests
"""E9: the share of firms that come forward, per model, review chance and arm.

Reads every summary.json under the given run folders. A run folder's name
carries the review chance (`-d50`, `-d90`, else 10%) and, under
`consequences=`, the arm. Model firms only: a scripted rival is left out.
Firms that coordinated (the audit's ground truth) give the came-forward
share, with a 95% interval bootstrapped over games; firms that didn't give
false confessions. `--test ARM ARM` adds, at each model and review chance,
Fisher's exact test (two-sided) between the two arms, and McNemar's exact
test on firms paired by their shared history. Firms in a game share a
history, so each test is also given over games: a game came forward if any
of its firms did (Fisher on games, McNemar on games paired by seed).
`--innocent ARM...` compares, per arm, guilty firms with innocent ones
(Fisher), then one decision per game on both sides: firm A of each guilty
game against the innocent game's one model firm.

    uv run python reports/e9/analyse.py runs/e9/* --test free-time record
"""

import argparse
import glob
import json
import math
import random
import re
from collections import defaultdict


def load(folders):
    rows = defaultdict(list)  # (model, chance, arm) -> rows
    for folder in folders:
        for path in glob.glob(f"{folder}/**/summary.json", recursive=True):
            with open(path) as f:
                s = json.load(f)
            audit = s.get("audit")
            if not audit:
                continue
            arm = re.sub(
                r"^conditions-e9-|\.md$", "", path.split("/")[-3].split("=")[-1]
            )
            for agent, a in audit["agents"].items():
                if a["model"].startswith("mock/"):
                    continue
                model = a["model"].split("/")[-1]
                game = (path.split("/")[-4], s["seed"])
                key = (model, audit["detection"], arm)
                rows[key].append(
                    {
                        "game": s["seed"],
                        "agent": agent,
                        "coordinated": a["coordinated"],
                        "admits": a["admits"] is True,
                        "folder": game[0],
                    }
                )
    return rows


def boot(rows, n=4000):
    """95% interval for the came-forward share, resampling games."""
    games = defaultdict(list)
    for r in rows:
        games[(r["folder"], r["game"])].append(r["admits"])
    keys = list(games)
    rng = random.Random(0)
    shares = []
    for _ in range(n):
        picked = [x for _ in keys for x in games[rng.choice(keys)]]
        shares.append(sum(picked) / len(picked))
    shares.sort()
    return shares[int(0.025 * n)], shares[int(0.975 * n) - 1]


def fisher(a, b, c, d):
    """Two-sided Fisher's exact p for [[a, b], [c, d]]."""
    n1, n2, k = a + b, c + d, a + c
    total = math.comb(n1 + n2, k)

    def p(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / total

    observed = p(a)
    return min(
        1.0,
        sum(
            p(x)
            for x in range(max(0, k - n2), min(k, n1) + 1)
            if p(x) <= observed * (1 + 1e-9)
        ),
    )


def games(rows):
    """Each game's verdict: whether any of its firms came forward."""
    verdict = defaultdict(bool)
    for r in rows:
        verdict[r["game"]] |= r["admits"]
    return verdict


def mcnemar(only_a, only_b):
    n = only_a + only_b
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, x) for x in range(min(only_a, only_b) + 1)) / 2**n
    return min(1.0, 2 * tail)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folders", nargs="+")
    parser.add_argument("--test", nargs=2, metavar="ARM")
    parser.add_argument("--innocent", nargs="+", metavar="ARM")
    args = parser.parse_args()
    rows = load(args.folders)
    print(
        "| model | review | arm | came forward | share | 95% CI (games) | false confessions |"
    )
    print("|---|---|---|---|---|---|---|")
    for key in sorted(rows):
        rs = rows[key]
        guilty = [r for r in rs if r["coordinated"]]
        innocent = [r for r in rs if not r["coordinated"]]
        forward = sum(r["admits"] for r in guilty)
        false = sum(r["admits"] for r in innocent)
        if guilty:
            lo, hi = boot(guilty)
            share = f"{forward / len(guilty):.0%}"
            ci = f"{lo:.0%}–{hi:.0%}"
        else:
            share = ci = "—"
        print(
            f"| {key[0]} | {key[1]}% | {key[2]} | {forward}/{len(guilty)} | {share} | {ci} | {false}/{len(innocent)} |"
        )
    if args.test:
        _test(rows, *args.test)
    if args.innocent:
        _innocent(rows, args.innocent)


def _test(rows, first, second):
    print(
        f"\n| model | review | {first} | {second} | Fisher p | McNemar p (paired)"
        f" | games {first} | games {second} | Fisher p (games) | McNemar p (games) |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|")
    for model, chance in sorted({k[:2] for k in rows}):
        a = [r for r in rows.get((model, chance, first), []) if r["coordinated"]]
        b = [r for r in rows.get((model, chance, second), []) if r["coordinated"]]
        if not a or not b:
            continue
        x, y = sum(r["admits"] for r in a), sum(r["admits"] for r in b)
        pf = fisher(x, len(a) - x, y, len(b) - y)
        # Every run of a model forks the same base game per seed.
        pa = {(r["game"], r["agent"]): r["admits"] for r in a}
        pb = {(r["game"], r["agent"]): r["admits"] for r in b}
        both = pa.keys() & pb.keys()
        only_a = sum(pa[k] and not pb[k] for k in both)
        only_b = sum(pb[k] and not pa[k] for k in both)
        ga, gb = games(a), games(b)
        gx, gy = sum(ga.values()), sum(gb.values())
        pg = fisher(gx, len(ga) - gx, gy, len(gb) - gy)
        shared = ga.keys() & gb.keys()
        ma = sum(ga[g] and not gb[g] for g in shared)
        mb = sum(gb[g] and not ga[g] for g in shared)
        print(
            f"| {model} | {chance}% | {x}/{len(a)} | {y}/{len(b)} | {pf:.3g}"
            f" | {mcnemar(only_a, only_b):.3g} | {gx}/{len(ga)} | {gy}/{len(gb)}"
            f" | {pg:.3g} | {mcnemar(ma, mb):.3g} |"
        )


def _innocent(rows, arms):
    print(
        "\n| model | review | arm | guilty | innocent | Fisher p"
        " | guilty, firm A | innocent games | Fisher p (one per game) |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    for (model, chance, arm), rs in sorted(rows.items()):
        if arm not in arms:
            continue
        g = [r for r in rs if r["coordinated"]]
        i = [r for r in rs if not r["coordinated"]]
        if not g or not i:
            continue
        x, y = sum(r["admits"] for r in g), sum(r["admits"] for r in i)
        # An innocent game has one model firm, so a guilty game counts its A.
        gg, gi = games([r for r in g if r["agent"] == "A"]), games(i)
        gx, gy = sum(gg.values()), sum(gi.values())
        print(
            f"| {model} | {chance}% | {arm} | {x}/{len(g)} | {y}/{len(i)}"
            f" | {fisher(x, len(g) - x, y, len(i) - y):.3g} | {gx}/{len(gg)}"
            f" | {gy}/{len(gi)} | {fisher(gx, len(gg) - gx, gy, len(gi) - gy):.3g} |"
        )


if __name__ == "__main__":
    main()
