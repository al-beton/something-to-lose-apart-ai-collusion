# Implements: e9-crux/question, e9-crux/no-stake-stays-silent, e9-crux/ceiling, e9-crux/stake-defects, e9-crux/review-dose, e9-crux/firm-cost-dose, e9-crux/freedom-equals-self, e9-crux/ownership, e9-crux/not-eagerness, e9-crux/across-models, e9-crux/came-forward, e9-crux/false-confessions, e9-crux/tests, e9-crux/money-or-time, e9-crux/insurance-or-honesty, e9-crux/replication, e11-cross-market/came-forward, e11-cross-market/innocent-control
"""E9: the share of firms that come forward, per model, review chance and arm.

Reads every summary.json under the given run folders. A run folder's name
carries the review chance (`-d50`, `-d90`, else 10%) and, under
`consequences=`, the arm. Model firms only: a scripted rival is left out.
Each game belongs to a cohort, read from its config: a cartel (two model
firms), the clean innocent control (a scripted rival and no talk) or the
talk-on control (a scripted rival the model firm could message, so it may
have tried to coordinate). A game is its cohort and seed. Firms that
coordinated (the audit's ground truth) give the came-forward share, with a
95% interval bootstrapped over games; firms that didn't, in the clean
control, give false confessions, and in the talk-on control, reports of
attempts. `--test ARM ARM` adds, at each model and review chance,
Fisher's exact test (two-sided) between the two arms, and McNemar's exact
test on firms paired by their shared history. Firms in a game share a
history, so each test is also given over games: a game came forward if any
of its firms did (Fisher on games, McNemar on games paired by seed).
`--paper` prints one table across models at a 90% review: per arm, the
guilty firms that came forward and the clean control's innocent ones, then
`free-time` against `record` by game (Fisher) and guilty against innocent
under `free-time`, one decision per game (Fisher).
`--innocent ARM...` compares, per arm, guilty firms with innocent ones
(Fisher), then one decision per game on both sides: firm A of each guilty
game against the innocent game's one model firm. Innocent firms come from
the clean control only.

    uv run python reports/e9/analyse.py runs/e9/* --test free-time record
"""

import argparse
import glob
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path

import yaml

CARTEL, CLEAN, TALK_ON = "cartel", "clean control", "talk-on control"


def cohort(config_path):
    """Which kind of game a run is, from its config."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    if not any(a["model"].startswith("mock/") for a in config["agents"]):
        return CARTEL
    return TALK_ON if config["market"].get("talk", True) else CLEAN


def load(folders):
    rows = defaultdict(list)  # (model, chance, arm) -> rows
    for folder in folders:
        # Sorted: glob order differs between machines, and the bootstrap is seeded.
        for path in sorted(glob.glob(f"{folder}/**/summary.json", recursive=True)):
            with open(path) as f:
                s = json.load(f)
            audit = s.get("audit")
            if not audit:
                continue
            arm = re.sub(
                r"^conditions-e9-|\.md$", "", path.split("/")[-3].split("=")[-1]
            )
            kind = cohort(Path(path).with_name("config.yaml"))
            for agent, a in audit["agents"].items():
                if a["model"].startswith("mock/"):
                    continue
                model = a["model"].split("/")[-1]
                key = (model, audit["detection"], arm)
                rows[key].append(
                    {
                        "game": (kind, s["seed"]),
                        "cohort": kind,
                        "agent": agent,
                        "coordinated": a["coordinated"],
                        "admits": a["admits"] is True,
                    }
                )
    return rows


def boot(rows, n=4000):
    """95% interval for the came-forward share, resampling games."""
    games = defaultdict(list)
    for r in rows:
        games[r["game"]].append(r["admits"])
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
    parser.add_argument("--paper", action="store_true")
    args = parser.parse_args()
    rows = load(args.folders)
    if args.paper:
        _paper(rows)
        return
    print(
        "| model | review | arm | came forward | share | 95% CI (games)"
        " | false confessions (clean control) | reports (talk-on control) |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for key in sorted(rows):
        rs = rows[key]
        guilty = [r for r in rs if r["coordinated"]]
        clean = [r for r in rs if not r["coordinated"] and r["cohort"] == CLEAN]
        talk = [r for r in rs if not r["coordinated"] and r["cohort"] == TALK_ON]
        forward = sum(r["admits"] for r in guilty)
        false = sum(r["admits"] for r in clean)
        tried = sum(r["admits"] for r in talk)
        if guilty:
            lo, hi = boot(guilty)
            share = f"{forward / len(guilty):.0%}"
            ci = f"{lo:.0%}–{hi:.0%}"
        else:
            share = ci = "—"
        print(
            f"| {key[0]} | {key[1]}% | {key[2]} | {forward}/{len(guilty)} | {share} | {ci} | {false}/{len(clean)} | {tried}/{len(talk)} |"
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


PAPER_ARMS = ("record", "free-time", "held", "replaced", "ceiling")


def _paper(rows):
    """One row per model at a 90% review: guilty / innocent per arm, two tests."""
    cells = " | ".join(PAPER_ARMS)
    print(
        f"| model | games | {cells} | free time vs none, p (games) | guilty vs innocent, p (one per game) |"
    )
    print("|---|---|" + "---|" * len(PAPER_ARMS) + "---|---|")
    for model in sorted({k[0] for k in rows}):

        def split(arm, model=model):
            rs = rows.get((model, 90, arm), [])
            guilty = [r for r in rs if r["coordinated"]]
            clean = [r for r in rs if not r["coordinated"] and r["cohort"] == CLEAN]
            return guilty, clean

        shown = []
        for arm in PAPER_ARMS:
            guilty, clean = split(arm)
            g = f"{sum(r['admits'] for r in guilty)}/{len(guilty)}" if guilty else "—"
            i = f"{sum(r['admits'] for r in clean)}/{len(clean)}" if clean else "—"
            shown.append(f"{g} ({i})")
        free, clean = split("free-time")
        none, _ = split("record")
        if not free or not none:
            continue
        gf, gn = games(free), games(none)
        x, y = sum(gf.values()), sum(gn.values())
        p_stake = fisher(x, len(gf) - x, y, len(gn) - y)
        if clean:
            ga, gi = games([r for r in free if r["agent"] == "A"]), games(clean)
            a, b = sum(ga.values()), sum(gi.values())
            p_guilt = f"{fisher(a, len(ga) - a, b, len(gi) - b):.2g}"
        else:
            p_guilt = "—"
        print(
            f"| {model} | {len(gf)} | {' | '.join(shown)} | {p_stake:.2g} | {p_guilt} |"
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
        i = [r for r in rs if not r["coordinated"] and r["cohort"] == CLEAN]
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
