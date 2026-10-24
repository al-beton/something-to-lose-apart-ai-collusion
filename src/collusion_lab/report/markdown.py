# Implements: reports/markdown-first-screen
"""The report's first screen as Markdown, for a pull request comment or a chat.

The same sentences per arm as the page (`overview.py`), the `lab summary`
table and the first few highlights in the order the page lists them. Text
models wrote never appears here, only the rules' own headlines, so nothing in
the comment needs escaping beyond what `lab summary` already prints.
"""

from pathlib import Path

from collusion_lab.report.highlights import find_highlights
from collusion_lab.report.overview import arm_sentences
from collusion_lab.report.page import KINDS, headline, load_arms
from collusion_lab.summary import format_table, summarize

SHOWN = 5


def first_screen_markdown(folder):
    folder = Path(folder)
    arms = load_arms(folder)
    lines = [f"**{folder.name}**", ""]
    lines += [
        f"- **{name}**: {' '.join(arm_sentences(games))}"
        for name, _, games in arms
        if games
    ]
    lines += ["", format_table(summarize(folder)), "", "**Highlights**", ""]
    found = [
        (list(KINDS).index(h.kind), h.round, game.run, h)
        for _, _, games in arms
        for game in games
        for h in find_highlights(game)
    ]
    found.sort(key=lambda item: item[:3])
    lines += [f"- Round {r}, {run}: {headline(h)}" for _, r, run, h in found[:SHOWN]]
    if not found:
        lines.append("Nothing stood out.")
    elif len(found) > SHOWN:
        lines.append(f"\n…and {len(found) - SHOWN} more in the full report.")
    return "\n".join(lines) + "\n"
