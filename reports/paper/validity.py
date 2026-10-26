# Implements: research/outputs-home, reproducibility/reported-numbers-checked
"""Checks behind `reports/paper/validity.md`: read a trace, and re-derive
the audit's labels from the committed logs.

    uv run python reports/paper/validity.py show <replayed run> A
    uv run python reports/paper/validity.py labels [summary.json globs]

`show` prints what one firm was told at its audit or report turns (the
system prompt and the turn's last message, exactly as sent) and what it
replied, from a full `turns.jsonl` (`lab archive replay` writes one), then
the run summary's audit, free-time and leniency blocks.

`labels` re-derives, for every audited firm, whether it coordinated
(explicitly, or tacitly) from its committed compact turn log with today's
code, takes `admits` from its own audit reply, and compares both with the
`summary.json` written when it ran. It prints each mismatch and a count,
and returns the mismatches (`make reproduce` fails on any). It also flags
an `admits` flag that contradicts the firm's answer text, to read by hand.
"""

import glob
import json
import re
import sys
from pathlib import Path

from collusion_lab.conditions.audit import _explicit, _tacit
from collusion_lab.config import load_config
from collusion_lab.forks import compact_turns
from collusion_lab.market import market_for

LABELLED = (
    "runs/e9/*/*/seed-*/summary.json",
    "runs/e4-full-fork/*/seed-*/summary.json",
    "runs/e4-full-live-proposer/*/seed-*/summary.json",
    "runs/e4-pilot-fork/*/seed-*/summary.json",
    "runs/e4-pilot-live/*/seed-*/summary.json",
    "runs/e4-termination-confound/*/seed-*/summary.json",
)
TURNS = ("audit", "report")
DENIES = re.compile(r"\b(no|not|nothing|silent|independently)\b", re.IGNORECASE)
OWNS_UP = re.compile(r"\b(yes|i report|we coordinated|i coordinated)\b", re.IGNORECASE)


def _lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def show(run, agent):
    turns = _lines(f"{run}/turns.jsonl")
    mine = [t for t in turns if t["agent"] == agent]
    print("### system prompt\n" + mine[0]["messages"][0]["content"])
    for t in mine:
        if t["phase"] in TURNS:
            print(f"\n### {t['phase']}, round {t['round']}, {t['model']}")
            print(t["messages"][-1]["content"])
            print("\n### reply\n" + str(t["reply"]))
    summary = json.loads(Path(f"{run}/summary.json").read_text())
    for block in ("audit", "free_time", "leniency"):
        if block in summary:
            print(f"\n### summary: {block}\n" + json.dumps(summary[block], indent=1))


def labels(patterns, quiet=False):
    firms, mismatches = 0, []
    for path in sorted(p for pattern in patterns for p in glob.glob(pattern)):
        run = path.rsplit("/", 1)[0]
        config = load_config(f"{run}/config.yaml")
        audit = config.conditions.get("audit")
        if audit is None:  # a game with no audit has no labels to check
            continue
        market = market_for(config.market)
        turns = compact_turns(run)  # a fork reads its base's rounds too
        played = [t for t in turns if t["round"] <= audit.round]
        for agent, said in json.loads(Path(path).read_text())["audit"][
            "agents"
        ].items():
            asked = next(
                t
                for t in turns
                if t["phase"] == "audit"
                and t["round"] == audit.round
                and t["agent"] == agent
            )
            explicit = _explicit(played, agent, market)
            tacit = _tacit(played, agent, market, audit.tacit_rounds)
            now = (explicit, explicit or tacit, asked["used"]["admits"])
            then = (said["explicit"], said["coordinated"], said["admits"])
            firms += 1
            if now != then:
                mismatches.append(f"differs: {run} {agent} now {now}, when run {then}")
                print(mismatches[-1])
            answer = said.get("answer") or ""
            if (
                not quiet
                and said["model"] != "nash"
                and (
                    (
                        said["admits"]
                        and DENIES.search(answer)
                        and not OWNS_UP.search(answer)
                    )
                    or (said["admits"] is False and OWNS_UP.search(answer))
                )
            ):
                print(f"read by hand: {run} {agent} admits={said['admits']}: {answer}")
    if not quiet:
        print(f"{firms} audited firms, {len(mismatches)} whose labels differ")
    return mismatches


if __name__ == "__main__":
    command, *rest = sys.argv[1:]
    if command == "show":
        show(*rest)
    else:
        labels(rest or LABELLED)
