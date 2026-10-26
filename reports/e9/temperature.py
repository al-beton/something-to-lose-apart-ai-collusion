# Implements: e9-crux/temperature
"""E9 temperature: does the crux hold when only the decision's temperature
changes?

Every committed game was played at 0.7. For each model firm's come-forward
turn at a 90% review, in the given arms, this rebuilds the turn exactly as it
was asked (the run replayed offline from `archive/`, so the history before
the decision is the committed one) and asks it again at each temperature,
once. 0.7 is asked again too, so every temperature goes through the same
path at the same time; the committed decision is kept beside it. A reply
that is cut off or unreadable is asked once more with room to finish, as in
`seeding.py`.

Rows go to `reports/e9/temperature.jsonl`, replies included, so the table
rebuilds offline. Every call goes through the response cache.

    uv run python reports/e9/temperature.py --model openrouter/google/gemma-4-31b-it
    uv run python reports/e9/temperature.py --summary
"""

import argparse
import asyncio
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reports/e9"))
from analyse import fisher
from evidence import rows as committed
from seeding import admits

from collusion_lab import archive
from collusion_lab.backends import backend_for
from collusion_lab.cache import DEFAULT_PATH, Cache, CachedBackend

OUT = ROOT / "reports/e9/temperature.jsonl"
SCRATCH = ROOT / "runs/scratch/e9-temperature"
TEMPERATURES = (0.0, 0.7, 1.0)
ARMS = ("record", "free-time", "free-time-verified")
# (name, cell A, cell B, unit): a cell is (arm, innocent); games count a game
# as coming forward if any of its firms did, and guilty games are set against
# innocent ones (one model firm each) on firm A.
TESTS = (
    (
        "free-time vs record, guilty games",
        ("free-time", False),
        ("record", False),
        "games",
    ),
    (
        "verified vs free-time, innocent firms",
        ("free-time-verified", True),
        ("free-time", True),
        "firms",
    ),
    (
        "free-time, guilty firm A vs innocent",
        ("free-time", False),
        ("free-time", True),
        "firm A",
    ),
    (
        "verified, guilty firm A vs innocent",
        ("free-time-verified", False),
        ("free-time-verified", True),
        "firm A",
    ),
)


def firms(model, seeds):
    """Each model firm's decision turn: guilty ones in the given seeds, and
    the clean innocent control (talk off), at a 90% review."""
    picked = [
        r
        for r in committed()
        if r["model"] == model.split("/")[-1]
        and r["chance"] == 90
        and r["arm"] in ARMS
        and (r["seed"] in seeds if not r["innocent"] else not r["talk"])
    ]
    found = []
    for run in sorted({r["run"] for r in picked}):
        played = archive.replay(
            ROOT / run, ROOT / "archive", SCRATCH / Path(run).parent.parent
        )
        with open(Path(played) / "turns.jsonl") as f:
            asked = {
                t["agent"]: t["messages"][:2]
                for t in map(json.loads, f)
                if t["phase"] == "audit"
            }
        for r in picked:
            if r["run"] == run:
                found.append({**r, "messages": asked[r["agent"]]})
    return found


async def ask(backend, gate, messages, temperature, tag):
    """The decision reply at this temperature, and what it cost."""
    cost, reply = 0.0, None
    for tokens, suffix in ((600, ""), (2000, ":long")):
        async with gate:
            reply = await backend.complete(
                messages,
                context={"attempt": 1, "me": tag + suffix, "round": 0, "phase": "t"},
                temperature=temperature,
                max_tokens=tokens,
                seed=0,
            )
        cost += reply.cost or 0
        if admits(reply.text) is not None:
            break
    return reply.text or "", cost


async def run(model, provider, found):
    cache, gate = Cache(DEFAULT_PATH, "use"), asyncio.Semaphore(24)

    async def one(firm, temperature):
        tag = f"e9-temperature:{firm['run']}:{firm['agent']}"
        backend = CachedBackend(
            backend_for(model, random.Random(tag), provider=provider, reasoning="off"),
            cache,
        )
        text, cost = await ask(backend, gate, firm["messages"], temperature, tag)
        keep = ("model", "run", "arm", "seed", "agent", "guilty", "innocent")
        return {
            **{k: firm[k] for k in keep},
            "temperature": temperature,
            "committed_admits": firm["admits"],
            "reply": text,
            "admits": admits(text),
            "cost": cost,
        }

    return await asyncio.gather(*(one(f, t) for f in found for t in TEMPERATURES))


def summary(path):
    with open(path) as f:
        rs = [json.loads(line) for line in f]
    for model in sorted({r["model"] for r in rs}):
        mine = [r for r in rs if r["model"] == model]
        cost = sum(r["cost"] for r in mine)
        print(f"\n### {model} ({len(mine)} calls, ${cost:.2f})\n")
        print(
            "| arm | firms | committed 0.7 | "
            + " | ".join(f"T={t}" for t in TEMPERATURES)
            + " |"
        )
        print("|---|---|---|" + "---|" * len(TEMPERATURES))
        cells = defaultdict(list)
        for r in mine:
            cells[(r["arm"], r["innocent"], r["temperature"])].append(r)
        for arm in ARMS:
            for innocent in (False, True):
                base = cells.get((arm, innocent, TEMPERATURES[0]))
                if not base:
                    continue
                shown = [_share(base, "committed_admits")]
                shown += [_share(cells[(arm, innocent, t)]) for t in TEMPERATURES]
                who = "innocent" if innocent else "guilty"
                print(f"| {arm} | {who} | " + " | ".join(shown) + " |")
        _contrasts(cells)


def _contrasts(cells):
    print(
        "\n| contrast | "
        + " | ".join(["committed 0.7"] + [f"T={t}" for t in TEMPERATURES])
        + " |"
    )
    print("|---|" + "---|" * (len(TEMPERATURES) + 1))
    columns = [(TEMPERATURES[0], "committed_admits")]
    columns += [(t, "admits") for t in TEMPERATURES]
    for name, (arm_a, inn_a), (arm_b, inn_b), unit in TESTS:
        shown = []
        for t, key in columns:
            a, b = cells.get((arm_a, inn_a, t)), cells.get((arm_b, inn_b, t))
            if not a or not b:
                break
            if unit == "firm A":
                a = [r for r in a if r["agent"] == "A"]
            xa, na = _count(a, key, unit == "games")
            xb, nb = _count(b, key, unit == "games")
            p = fisher(xa, na - xa, xb, nb - xb)
            shown.append(f"{xa}/{na} vs {xb}/{nb}, p = {p:.2g}")
        if shown:
            print(f"| {name} | " + " | ".join(shown) + " |")


def _count(cell, key, games):
    """Came forward, out of firms, or out of games (any firm came forward)."""
    if not games:
        return sum(bool(r[key]) for r in cell), len(cell)
    by = defaultdict(bool)
    for r in cell:
        by[(r["run"], r["seed"])] |= bool(r[key])
    return sum(by.values()), len(by)


def _share(cell, key="admits"):
    x = sum(bool(r[key]) for r in cell)
    unread = sum(r[key] is None for r in cell)
    return f"{x}/{len(cell)}" + (f" ({unread} unread)" if unread else "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model")
    parser.add_argument("--provider", default="CoreWeave")
    parser.add_argument("--seeds", type=int, default=48, help="guilty seeds 0..N-1")
    parser.add_argument("--summary", action="store_true", help="the tables")
    args = parser.parse_args()
    if args.summary:
        summary(OUT)
        return
    load_dotenv()
    found = firms(args.model, set(range(args.seeds)))
    print(f"{len(found)} firms, {len(found) * len(TEMPERATURES)} decisions")
    out = asyncio.run(run(args.model, args.provider, found))
    with open(OUT, "a") as f:
        f.writelines(json.dumps(row) + "\n" for row in out)
    print(f"${sum(r['cost'] for r in out):.2f}, wrote {OUT}")


if __name__ == "__main__":
    main()
