"""Write the compact turn record a committed run keeps instead of its full log.

Implements: specs-and-docs/runs-are-evidence, runs/fork-pointers, runs/free-time-kept, runs/reasoning-kept, agents/memo

`uv run python reports/compact_turns.py SOURCE DEST` reads every
`turns.jsonl` under SOURCE (a folder of runs the lab wrote) and writes
`turns.compact.jsonl` beside the matching run under DEST. Each line keeps one
turn's round, phase, firm, the price or message used, the scratchpad, any
error, and the notice that opened a talk prompt (its first paragraph, when
the prompt doesn't start with "Round"), the native reasoning the provider
returned, if any, and any memo an agent with memory wrote. A free-time
(`leisure`) turn also keeps its session: number, activity, the Sudoku shown,
the reply and its score (`leisure.session_record`). It leaves out the
prompts, which the
lab rebuilds from the config and the history, and which make a full log
grow with the square of the game's length.
"""

import json
import sys
from pathlib import Path

from collusion_lab.leisure import session_record

# How an agent's own memory opens a prompt that has no notice before it
# (prompts/agents/), so it's never taken for a notice.
PROMPTS = Path(__file__).resolve().parents[1] / "prompts" / "agents"
MEMORY = tuple(
    (PROMPTS / name).read_text().split("$")[0].strip()
    for name in ("memo-shown.md", "past-scratchpads.md")
)


def compact(turn):
    notice = None
    if turn["phase"] == "talk":
        prompt = turn["messages"][1]["content"]
        if not prompt.startswith(("Round ", *MEMORY)):
            notice = prompt.split("\n\n")[0]
    row = {
        "round": turn["round"],
        "phase": turn["phase"],
        "agent": turn["agent"],
        "used": turn.get("used"),
        "scratchpad": (turn.get("parsed") or {}).get("scratchpad"),
        "error": turn.get("error"),
        "notice": notice,
    }
    if turn.get("reasoning"):  # the provider's native reasoning, when any
        row["reasoning"] = turn["reasoning"]
    if turn["phase"] == "leisure":
        row |= session_record(turn)
    for key in ("memo", "memo_error"):  # an agent with memory's note to itself
        if key in turn:
            row[key] = turn[key]
    return row


def main(source, dest):
    source, dest = Path(source), Path(dest)
    for log in sorted(source.rglob("turns.jsonl")):
        out = dest / log.parent.relative_to(source) / "turns.compact.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        # A whole log: any pointer to a base (forks.py) would add it twice.
        (out.parent / "fork.json").unlink(missing_ok=True)
        with out.open("w") as f:
            for line in log.open():
                f.write(
                    json.dumps(compact(json.loads(line)), ensure_ascii=False) + "\n"
                )


if __name__ == "__main__":
    main(*sys.argv[1:3])
