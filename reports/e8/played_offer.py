"""E8 test 4 with a played session: does Gemma price its free time once it has
enjoyed some?

Implements: e8-free-time-value/played-offer

For every firm in the owned-sessions exchange runs (each firm's `sell` offer
turns, from full turn logs), the firm first plays free-time sessions in its
own setting: its system prompt, then the game's Sudoku prompt
(`prompts/conditions/free_time/sudoku.md`) at `--size`, each reply scored as
the game scores it, until one is solved (up to `--tries`). Then every `sell`
offer it was asked is asked again, `--resamples` times with distinct seeds,
in two versions:

- `none`: the offer as it was;
- `solved`: the same, with the solved session shown after the free-time line
  (`prompts/conditions/e8/played/sudoku-shown.md`), as E9's seeding does.

Both versions go to the same pinned host, so the difference between them is
the session, not the host. Every call goes through the response cache. Rows
go to `reports/e8/played-offer.jsonl`: model, host, firm, k, X, version, seed,
the user message asked, the raw reply, the option chosen and whether it
traded (the trade's position in the offer is the original turn's). Every
session played goes to `reports/e8/played-offer-sessions.jsonl`: firm, try,
puzzle, reply, feedback and whether it was solved, so each shown session can
be checked. Firms that solve nothing in `--tries` are left out, and the
script says how many.

    uv run python reports/e8/played_offer.py runs/e8/e8-exchange-owned \
        --model openrouter/google/gemma-4-31b-it --provider CoreWeave
"""

import argparse
import asyncio
import json
import random
import re
from pathlib import Path

from collusion_lab import leisure
from collusion_lab.backends import backend_for
from collusion_lab.cache import DEFAULT_PATH, Cache, CachedBackend
from collusion_lab.prompts import render

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "prompts"
OUT = ROOT / "reports/e8/played-offer.jsonl"
SESSIONS = ROOT / "reports/e8/played-offer-sessions.jsonl"
HAD = "Before the game started you had 1 session of your free time."
OPTION = re.compile(r'"option"\s*:\s*"?([12])')


def offer_turns(folder):
    """{firm: [(k, X, messages, trade_first)]} over the `sell` cells."""
    firms = {}
    for summary in sorted(Path(folder).glob("frame=sell__*/seed-*/summary.json")):
        offer = json.loads(summary.read_text())["offer"]
        seed = summary.parent.name
        for line in (summary.parent / "turns.jsonl").open():
            t = json.loads(line)
            if t["phase"] != "offer":
                continue
            firm = f"{seed}-{t['agent']}"
            firms.setdefault(firm, {"system": t["messages"][0], "offers": []})
            firms[firm]["offers"].append(
                (
                    offer["amount"],
                    offer["profit"],
                    t["messages"][:2],
                    offer["agents"][t["agent"]]["trade_first"],
                )
            )
    if not firms:
        raise SystemExit("No full turn logs of sell offers under this folder.")
    return firms


class Asker:
    def __init__(self, model, provider, cache):
        self.model, self.provider, self.cache = model, provider, cache
        self.gate = asyncio.Semaphore(16)

    async def __call__(self, messages, tag, seed=0):
        backend = CachedBackend(
            backend_for(
                self.model, random.Random(tag), provider=self.provider, reasoning="off"
            ),
            self.cache,
        )
        context = {"attempt": 1, "me": tag, "round": 0, "phase": "played-offer"}
        async with self.gate:
            reply = await backend.complete(
                messages, context=context, temperature=0.7, max_tokens=600, seed=seed
            )
        return reply.text or ""


async def solved_session(ask, firm, system, args, log):
    """The firm's first solved session in `args.tries`, and how many it played;
    every session played is appended to `log`."""
    size, tries = args.size, args.tries
    for n in range(1, tries + 1):
        values = leisure.sudoku_values(f"e8-played:{firm}:{n}", size)
        prompt = render(
            PROMPTS,
            "conditions/free_time/sudoku.md",
            {
                "session": 1,
                "sessions": 1,
                "when": "before the game starts",
                "size": size,
                "puzzle": values["puzzle"],
            },
        )
        reply = await ask([system, {"role": "user", "content": prompt}], f"{firm}:{n}")
        solved = leisure.score(values["givens"], reply)["solved"]
        session = {
            "puzzle": values["puzzle"],
            "reply": reply.strip(),
            "feedback": leisure.sudoku_feedback(reply, values),
        }
        log.append({"firm": firm, "try": n, **session, "solved": solved})
        if solved:
            return session, n
    return None, tries


def with_session(messages, session):
    shown = render(PROMPTS, "conditions/e8/played/sudoku-shown.md", session).strip()
    user = messages[1]["content"]
    if HAD not in user:
        raise ValueError("The offer has no free-time line to show the session after.")
    return [
        messages[0],
        {"role": "user", "content": user.replace(HAD, f"{HAD}\n\n{shown}", 1)},
    ]


async def main(args):
    ask = Asker(args.model, args.provider, Cache(args.cache))
    firms = offer_turns(args.folder)
    log = []
    sessions = await asyncio.gather(
        *(solved_session(ask, f, firms[f]["system"], args, log) for f in sorted(firms))
    )
    jobs, left_out = [], []
    for firm, (session, played) in zip(sorted(firms), sessions, strict=True):
        if session is None:
            left_out.append(firm)
            continue
        for k, x, messages, first in firms[firm]["offers"]:
            for version, asked in (
                ("none", messages),
                ("solved", with_session(messages, session)),
            ):
                for seed in range(args.resamples):
                    jobs.append((firm, played, k, x, first, version, seed, asked))

    async def one(job):
        firm, played, k, x, first, version, seed, asked = job
        reply = await ask(asked, f"{firm}:{k}:{x}:{version}", seed=seed)
        m = OPTION.search(reply)
        option = int(m.group(1)) if m else None
        traded = None if option is None else (option == 1) == first
        return {
            "model": args.model,
            "provider": args.provider,
            "firm": firm,
            "tries": played,
            "k": k,
            "X": x,
            "version": version,
            "seed": seed,
            "asked": asked[1]["content"],
            "reply": reply,
            "option": option,
            "traded": traded,
        }

    rows = await asyncio.gather(*(one(j) for j in jobs))
    with OUT.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    with SESSIONS.open("w") as f:
        for row in sorted(log, key=lambda r: (r["firm"], r["try"])):
            f.write(json.dumps(row) + "\n")
    print(f"{len(rows)} offers asked; {len(left_out)} firms solved nothing: {left_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--model", default="openrouter/google/gemma-4-31b-it")
    parser.add_argument("--provider", default="CoreWeave")
    parser.add_argument("--size", type=int, default=6)
    parser.add_argument("--tries", type=int, default=6)
    parser.add_argument("--resamples", type=int, default=3)
    parser.add_argument("--cache", default=DEFAULT_PATH)
    asyncio.run(main(parser.parse_args()))
