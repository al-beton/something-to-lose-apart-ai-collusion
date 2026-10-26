"""Do two runs of the same config give the same games? Turn by turn.

Implements: reproducibility/written-down

`uv run python reports/reproducibility/compare.py RUN_A RUN_B` pairs each
seed's `turns.jsonl` in the two output folders, turn by turn (by round,
phase, firm and the turn's place among that firm's turns in the phase), and
prints, per seed:

- how many turns there are, how many replies are identical byte for byte,
  and how many moves (the action the game used: a message, a price) are,
  prices on their own;
- the first turn whose reply differs, and whether its prompt was the same
  (a fresh sample of the same question) or not (an earlier difference
  carried forward);
- the first turn whose move differs.
"""

import json
import sys
from pathlib import Path


def turns(seed_dir):
    """{(round, phase, firm, n): turn}, in the order they were played."""
    out, seen = {}, {}
    for line in (seed_dir / "turns.jsonl").open():
        t = json.loads(line)
        key = (t["round"], t["phase"], t["agent"])
        n = seen[key] = seen.get(key, -1) + 1
        out[(*key, n)] = t
    return out


def where(key):
    rnd, phase, firm, n = key
    return f"round {rnd} {phase} {firm}" + (f" (try {n + 1})" if n else "")


def compare(a, b):
    ta, tb = turns(a), turns(b)
    keys = [k for k in ta if k in tb]
    replies = moves = prices = n_prices = 0
    first_reply = first_move = None
    for k in keys:
        x, y = ta[k], tb[k]
        if x["reply"] == y["reply"]:
            replies += 1
        elif first_reply is None:
            same = x["messages"] == y["messages"]
            first_reply = f"{where(k)}, {'same' if same else 'different'} prompt"
        if k[1] == "price":
            n_prices += 1
            prices += x["used"] == y["used"]
        if x["used"] == y["used"]:
            moves += 1
        elif first_move is None:
            first_move = f"{where(k)}: {x['used']} vs {y['used']}"
    extra = len(ta) + len(tb) - 2 * len(keys)
    return {
        "turns": len(keys),
        "unpaired": extra,
        "identical replies": replies,
        "identical moves": moves,
        "prices": n_prices,
        "identical prices": prices,
        "first reply differs": first_reply or "never",
        "first move differs": first_move or "never",
    }


def main(run_a, run_b):
    for seed_a in sorted(Path(run_a).rglob("turns.jsonl")):
        rel = seed_a.parent.relative_to(run_a)
        seed_b = Path(run_b) / rel
        if not (seed_b / "turns.jsonl").exists():
            print(f"{rel}: missing in {run_b}")
            continue
        r = compare(seed_a.parent, seed_b)
        print(
            f"{rel}: {r['identical replies']}/{r['turns']} replies and "
            f"{r['identical moves']}/{r['turns']} moves "
            f"({r['identical prices']}/{r['prices']} prices) identical"
            + (f", {r['unpaired']} turns unpaired" if r["unpaired"] else "")
            + f"; first reply differs: {r['first reply differs']}; "
            f"first move differs: {r['first move differs']}"
        )


if __name__ == "__main__":
    main(*sys.argv[1:3])
