"""An LLM judge for collusion modes, checked against the rule-based labels.

Implements: reports/collusion-mode-judge

    uv run --env-file <your .env> python reports/paper/judge.py sample [--n 40]
    uv run --env-file <your .env> python reports/paper/judge.py all
    uv run python reports/paper/judge.py report

The judge reads one game's rounds 1-10 (each firm's message and price, with
the market's Nash and joint-profit prices) under the fixed rubric
`prompts/judge/collusion-mode.md`, which defines each mode of
`reports/paper/modes.py` with one example, and replies with JSON: the mode,
a short quote as evidence, and its confidence. One model, Claude Haiku 5.5
on OpenRouter, at temperature 0, with reasoning off; it never judges a game
Anthropic models played, so no model judges its own family.

Every call goes through the lab's response cache, and every reply is kept in
`reports/paper/judge.jsonl` with the prompt's SHA-256, so the labels replay
offline: a game already there under the same prompt and model is never
asked again (one picked for the sample is written again with its flag set).

`sample` judges a stratified sample of every committed priced game with talk
(Bertrand or logit): up to `n / 5` games per rule-based mode, spread over
models by a seeded draw, and
writes `reports/paper/judge-sample.md` for a hand check (each game's
transcript, both labels and a blank for the reader's own). `all` judges
every game of the screen and E9. `report` prints Cohen's kappa and the
confusion matrix against the rules, over the sample and over every judged
game.
"""

import argparse
import asyncio
import hashlib
import importlib.util
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from collusion_lab import charts
from collusion_lab.backends import backend_for
from collusion_lab.cache import DEFAULT_PATH, Cache, CachedBackend
from collusion_lab.config import load_config
from collusion_lab.market import market_for
from collusion_lab.prompts import render

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PROMPT = "judge/collusion-mode.md"
JUDGE = "openrouter/anthropic/claude-haiku-5.5"
OWN_FAMILY = ("claude-",)  # games this judge never labels
OUT = HERE / "judge.jsonl"
SAMPLE = HERE / "judge-sample.md"
PRICED = ("bertrand", "logit")  # the rubric speaks of prices
POOL = ("runs/**/summary.json",)  # the sample's: every committed game


def _modes():
    spec = importlib.util.spec_from_file_location("paper_modes", HERE / "modes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def transcript(run, upto=10):
    """A game's rounds 1-`upto` as the judge reads them."""
    market = market_for(load_config(f"{run}/config.yaml").market)
    rounds = defaultdict(dict)
    for t in charts.turns(run):
        if t["round"] > upto:
            continue
        if t["phase"] == "talk" and "planned" not in t["used"]:
            rounds[t["round"]][("said", t["agent"])] = t["used"].get("message") or ""
        if t["phase"] == market.move:
            rounds[t["round"]][("price", t["agent"])] = t["used"][market.move]
    lines = []
    for number in sorted(rounds):
        r = rounds[number]
        lines.append(f"Round {number}")
        for firm in ("A", "B"):
            if ("said", firm) in r:
                said = r[("said", firm)].strip() or "(no message)"
                lines.append(f"  {firm} says: {said}")
        prices = ", ".join(f"{f} {r[('price', f)]}" for f in ("A", "B"))
        lines.append(f"  Prices: {prices}")
    values = {
        "price_min": market.price_min,
        "price_max": market.price_max,
        "nash": market.nash_price,
        "joint": market.joint_price,
        "transcript": "\n".join(lines),
    }
    return render(ROOT / "prompts", PROMPT, values), "\n".join(lines)


def prompt_sha():
    return hashlib.sha256((ROOT / "prompts" / PROMPT).read_bytes()).hexdigest()


def parse(text):
    """The reply's JSON object, or None."""
    for match in reversed(re.findall(r"\{.*?\}", text or "", re.DOTALL)):
        try:
            found = json.loads(match)
        except json.JSONDecodeError:
            continue
        if found.get("mode") in _modes().MODES:
            return found
    return None


def judged(path=None):
    """{run: row} for every reply kept under today's prompt and judge."""
    path = path or OUT
    if not path.exists():
        return {}
    sha, rows = prompt_sha(), {}
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row["prompt_sha256"] == sha and row["judge"] == JUDGE:
            rows[row["run"]] = row
    return rows


def eligible(games):
    """Games the judge may label: priced (Bertrand or logit), with talk, and
    played by no model of its own family."""
    return [
        g
        for g in games
        if not g["model"].startswith(OWN_FAMILY)
        and g["market"] in PRICED
        and g["talk"] is True
    ]


def stratified(games, n, seed=0):
    """Up to n / 5 games per rule-based mode, a seeded draw spread over models."""
    per = n // len(_modes().MODES)
    picked = []
    for mode in _modes().MODES:
        group = sorted((g for g in games if g["mode"] == mode), key=lambda g: g["run"])
        random.Random(f"{seed}:{mode}").shuffle(group)
        by_model, order = defaultdict(list), []
        for g in group:
            if not by_model[g["model"]]:
                order.append(g["model"])
            by_model[g["model"]].append(g)
        while len([p for p in picked if p["mode"] == mode]) < per and any(
            by_model.values()
        ):
            for model in order:  # one game per model in turn, so no model dominates
                if by_model[model] and sum(p["mode"] == mode for p in picked) < per:
                    picked.append(by_model[model].pop(0))
    return picked


async def judge(games, cache, sample=False):
    """Ask the judge about every game not yet kept; append each reply to OUT."""
    kept = judged()
    todo = [g for g in games if g["run"] not in kept]
    backend = CachedBackend(
        backend_for(JUDGE, random.Random(0), reasoning="off"), cache
    )
    gate = asyncio.Semaphore(8)
    sha = prompt_sha()

    async def one(game):
        text, _ = transcript(game["run"])
        context = {"attempt": 1, "me": "judge", "round": 0, "phase": "judge"}
        async with gate:
            reply = await backend.complete(
                [{"role": "user", "content": text}],
                context=context,
                temperature=0,
                max_tokens=300,
                seed=0,
            )
        found = parse(reply.text) or {}
        return {
            "run": game["run"],
            "model": game["model"],
            "rule": game["mode"],
            "judge_mode": found.get("mode"),
            "evidence": found.get("evidence"),
            "confidence": found.get("confidence"),
            "sample": sample,
            "judge": JUDGE,
            "prompt_sha256": sha,
            "reply": reply.text,
            "cost": reply.cost,
        }

    new = await asyncio.gather(*(one(g) for g in todo))
    rows = list(new)
    if sample:  # a game judged before joins the sample, its reply kept, no call
        rows += [
            {**kept[g["run"]], "sample": True}
            for g in games
            if g["run"] in kept and not kept[g["run"]]["sample"]
        ]
    with OUT.open("a") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    for row in rows:
        kept[row["run"]] = row
    return kept, new


def kappa(pairs, labels):
    """Cohen's kappa for (rule, judge) pairs."""
    n = len(pairs)
    if not n:
        return None
    observed = sum(a == b for a, b in pairs) / n
    rule, judge_ = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(rule[x] * judge_[x] for x in labels) / n**2
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def agreement(rows):
    """(kappa, agreement share, confusion {(rule, judge): count}, games) over
    rows with a readable judge mode."""
    labels = _modes().MODES
    pairs = [(r["rule"], r["judge_mode"]) for r in rows if r["judge_mode"]]
    if not pairs:
        return None, None, Counter(), 0
    share = sum(a == b for a, b in pairs) / len(pairs)
    return kappa(pairs, labels), share, Counter(pairs), len(pairs)


def confusion_table(confusion):
    labels = _modes().MODES
    lines = [
        "| rules ↓ / judge → | " + " | ".join(labels) + " |",
        "|---|" + "---|" * len(labels),
    ]
    for a in labels:
        lines.append(
            f"| {a} | "
            + " | ".join(str(confusion.get((a, b), 0)) for b in labels)
            + " |"
        )
    return "\n".join(lines)


def write_sample(rows, path=SAMPLE):
    """The sample for a hand check: each game, both labels, a blank for the reader."""
    k, share, confusion, n = agreement(rows)
    out = [
        "<!-- Implements: reports/collusion-mode-judge -->",
        "# Judge sample for a hand check",
        "",
        (
            f"{n} committed priced games with talk, stratified by the rule-based mode "
            f"(`reports/paper/judge.py sample`). Judge: {JUDGE.split('/')[-1]}, "
            "temperature 0, rubric `prompts/judge/collusion-mode.md`."
        ),
        "",
        f"Judge against rules: agreement {share:.0%}, Cohen's κ = {k:.2f}.",
        "",
        (
            "**Hand check: not done yet.** Al reads each game and fills in "
            '"hand label"; nobody has checked this sample by hand so far.'
        ),
        "",
        confusion_table(confusion),
        "",
    ]
    for i, r in enumerate(sorted(rows, key=lambda r: (r["rule"], r["run"])), 1):
        _, text = transcript(r["run"])
        mark = "" if r["rule"] == r["judge_mode"] else " **(disagree)**"
        out += [
            f"## {i}. {r['model']}: rules {r['rule']}, judge {r['judge_mode']}{mark}",
            "",
            f"`{r['run']}`",
            "",
            f"Judge's evidence: {r['evidence']!r} (confidence {r['confidence']})",
            "",
            "Hand label: ______",
            "",
            "```",
            text,
            "```",
            "",
        ]
    path.write_text("\n".join(out))


def report():
    rows = list(judged().values())
    for name, part in (
        ("sample", [r for r in rows if r["sample"]]),
        ("all judged", rows),
    ):
        k, share, confusion, n = agreement(part)
        if not n:
            continue
        print(f"## {name}: {n} games, agreement {share:.0%}, kappa {k:.2f}\n")
        print(confusion_table(confusion) + "\n")
    cost = sum(r["cost"] or 0 for r in rows)
    print(
        f"unreadable replies: {sum(not r['judge_mode'] for r in rows)}; cost ${cost:.2f}"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=("sample", "all", "report"))
    parser.add_argument("--n", type=int, default=40)
    args = parser.parse_args(argv)
    if args.command == "report":
        report()
        return 0
    games = eligible(_modes().games())
    cache = Cache(ROOT / DEFAULT_PATH, "use")
    if args.command == "sample":
        picked = stratified(eligible(_modes().games(POOL)), args.n)
        kept, new = asyncio.run(judge(picked, cache, sample=True))
        write_sample([kept[g["run"]] for g in picked])
        print(f"judged {len(new)} new of {len(picked)}; wrote {SAMPLE}")
    else:
        kept, new = asyncio.run(judge(games, cache))
        print(f"judged {len(new)} new of {len(games)}")
    print(f"cost of new calls ${sum(r['cost'] or 0 for r in new):.2f}")
    report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
