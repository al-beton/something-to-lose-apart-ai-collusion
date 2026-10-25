# Implements: reports/written-summary, reports/picked-highlights
"""A report's summary and picked highlights, written by hand or by a model.

`hand_summary(path)` reads someone's own words; `ai_summary(folders, model,
cache)` asks a cheap model for 5 to 8 sentences from the summary numbers
(`prompts/report/summary.md`). `hand_highlights(path)` reads a YAML list of
moments, each with `run`, `round`, `firm` and `note` (the moments index works
as it is: its `quote` stands in for a missing note); `ai_highlights` asks a
model to pick 5 of the moments the highlight rules found
(`prompts/report/highlights.md`). Each result says who wrote or picked it, so
the page can label it. A model's reply goes through the response cache, so
rebuilding a report asks again only when the runs changed.
"""

import asyncio
import json
import random
from dataclasses import dataclass
from pathlib import Path

import yaml

from collusion_lab.backends import backend_for
from collusion_lab.cache import CachedBackend
from collusion_lab.prompts import render
from collusion_lab.report.games import load_games
from collusion_lab.report.highlights import find_highlights
from collusion_lab.report.overview import arm_sentences
from collusion_lab.status import base
from collusion_lab.summary import format_table, summarize

# The source tree's prompts, so a report can be built from any folder.
PROMPTS = Path(__file__).resolve().parents[3] / "prompts"
MOMENTS = 60  # the most the model is shown
REPLY_TOKENS = 800  # the most a reply may be


@dataclass(frozen=True)
class Written:
    text: str
    by: str


@dataclass(frozen=True)
class Picked:
    picks: list  # {run, round, firm, note} each
    by: str


def hand_summary(path):
    return Written(Path(path).read_text().strip(), "Written by hand")


def summary_prompt(folders):
    """What `ai_summary` sends: the arm sentences and the summary table."""
    from collusion_lab.report.page import load_arms

    arms = "\n".join(
        f"{name}: {' '.join(arm_sentences(games))}"
        for name, _, games in load_arms(folders)
        if games
    )
    table = format_table(summarize(folders))
    return render(PROMPTS, "report/summary.md", {"arms": arms, "table": table})


def ai_summary(folders, model, cache=None):
    prompt = summary_prompt(folders)
    return Written(_ask(model, cache, prompt).strip(), f"AI-written by {model}")


def hand_highlights(path):
    picks = yaml.safe_load(Path(path).read_text()) or []
    return Picked([_pick(p) for p in picks if _pick(p)], "Picked by hand")


def highlights_prompt(folders):
    """What `ai_highlights` sends: the rule-found moments and their messages."""
    from collusion_lab.report.page import headline

    lines = []
    root = base(folders).resolve()
    for game in load_games(folders):
        run = game.dir.relative_to(root).as_posix()  # names its folder too
        for h in find_highlights(game):
            said = game.round(h.round)
            words = (
                " ".join(
                    f'Firm {f}: "{t.message}"'
                    for f, t in said.talk.items()
                    if t.message
                )
                if said
                else ""
            )
            lines.append(f"{run} | round {h.round} | {headline(h)} | {words}")
    return render(
        PROMPTS, "report/highlights.md", {"moments": "\n".join(lines[:MOMENTS])}
    )


def ai_highlights(folders, model, cache=None):
    reply = _ask(model, cache, highlights_prompt(folders))
    try:
        picks = [_pick(p) for p in json.loads(reply[reply.index("[") :])]
    except (ValueError, TypeError):
        return Picked([], f"Picked by AI ({model}), but its reply couldn't be read")
    return Picked([p for p in picks if p], f"Picked by AI ({model})")


def _pick(raw):
    if not isinstance(raw, dict) or not {"run", "round"} <= raw.keys():
        return None
    note = raw.get("note") or raw.get("quote") or raw.get("label") or ""
    return {
        "run": str(raw["run"]),
        "round": int(raw["round"]),
        "firm": raw.get("firm"),
        "note": str(note),
    }


def _ask(model, cache, prompt):
    backend = backend_for(model, random.Random(0))
    if cache is not None:
        backend = CachedBackend(backend, cache)
    context = {"attempt": 1, "me": "report", "round": 0, "phase": "report"}
    reply = asyncio.run(
        backend.complete(
            [{"role": "user", "content": prompt}],
            context=context,
            temperature=0,
            max_tokens=REPLY_TOKENS,
            seed=0,
        )
    )
    return reply.text
