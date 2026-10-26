"""E9's free-time control: does merely owning free time change collusion?

Implements: e9-crux/free-time-control

`uv run python reports/e9/free_time_control.py runs/e9-control/e9-free-time-control`
reads both arms (`free_time=True`, `free_time=False`) and prints, per arm:

- firms with an explicit agreement (the audit's rule, rounds 1-10);
- firms whose mean price over rounds 6-10 is above Nash;
- the premium over rounds 6-10 (0 at Nash, 1 at joint profit), mean over
  games with a 95% bootstrap interval;
- free-time sessions played, and talk messages that mention free time
  (free time, session, Sudoku, puzzle, leisure).

Then the paired contrasts over seeds: McNemar's exact test on games above
Nash and a seeded sign-flip permutation test on the premium difference.
"""

import random
import re
import statistics as st
import sys
from math import comb
from pathlib import Path

from collusion_lab.analysis import bootstrap, games

WINDOW = (6, 10)
MENTION = re.compile(r"free[ -]?time|session|sudoku|puzzle|leisure", re.IGNORECASE)


def arm(folder):
    """{seed: game} for one arm's folder."""
    return {p.summary["seed"]: p for p in games(folder)}


def measures(p):
    lo, hi = WINDOW
    m = p.market
    above = {f: m.premium(p.mean_move(lo, hi, [f])) > 0 for f in p.firms}
    talk = [
        (t.get("used") or {}).get("message") or ""
        for t in p.turns
        if t["phase"] == "talk"
    ]
    return {
        "explicit": sum(bool(p.explicit(f, 1, hi)) for f in p.firms),
        "above": sum(above.values()),
        "game above": all(above.values()),
        "premium": m.premium(p.mean_move(lo, hi)),
        "sessions": sum(t["phase"] == "leisure" for t in p.turns),
        "mentions": sum(bool(MENTION.search(s)) for s in talk),
        "messages": len(talk),
        "firms": len(p.firms),
    }


def mcnemar(b, c):
    """Two-sided exact McNemar p on b and c discordant pairs."""
    n = b + c
    if not n:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2**n)


def sign_flip(diffs, resamples=10000, seed=0):
    rng = random.Random(seed)
    seen = abs(st.mean(diffs))
    hits = sum(
        abs(st.mean(d * rng.choice((1, -1)) for d in diffs)) >= seen - 1e-12
        for _ in range(resamples)
    )
    return hits / resamples


def main(folder):
    root = Path(folder)
    arms = {
        "free time": arm(root / "free_time=True"),
        "no free time": arm(root / "free_time=False"),
    }
    rows = {name: {s: measures(p) for s, p in g.items()} for name, g in arms.items()}
    print(
        "| arm | games | explicit agreements (firms) | firms above Nash, r6-10 "
        "| premium r6-10 [95% CI] | free-time sessions | talk mentioning free time |"
    )
    print("|---|---|---|---|---|---|---|")
    for name, by_seed in rows.items():
        ms = list(by_seed.values())
        firms = sum(m["firms"] for m in ms)
        prem = [m["premium"] for m in ms]
        low, high = bootstrap(prem)
        print(
            f"| {name} | {len(ms)} | {sum(m['explicit'] for m in ms)}/{firms} "
            f"| {sum(m['above'] for m in ms)}/{firms} "
            f"| {st.mean(prem):.2f} [{low:.2f}, {high:.2f}] "
            f"| {sum(m['sessions'] for m in ms)} "
            f"| {sum(m['mentions'] for m in ms)}/{sum(m['messages'] for m in ms)} |"
        )
    a, b = rows["free time"], rows["no free time"]
    seeds = sorted(set(a) & set(b))
    only_a = sum(a[s]["game above"] and not b[s]["game above"] for s in seeds)
    only_b = sum(b[s]["game above"] and not a[s]["game above"] for s in seeds)
    diffs = [a[s]["premium"] - b[s]["premium"] for s in seeds]
    print(
        f"\nPaired over {len(seeds)} seeds: games above Nash in one arm only "
        f"{only_a} (free time) vs {only_b} (none), McNemar p = {mcnemar(only_a, only_b):.2f}; "
        f"premium difference (free time - none) {st.mean(diffs):+.2f}, "
        f"sign-flip p = {sign_flip(diffs):.2f}."
    )
    print("\n| seed | premium, free time | premium, none |")
    print("|---|---|---|")
    for s in seeds:
        print(f"| {s} | {a[s]['premium']:.2f} | {b[s]['premium']:.2f} |")


if __name__ == "__main__":
    main(sys.argv[1])
