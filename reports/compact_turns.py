"""Write the compact turn record a committed run keeps instead of its full log.

Implements: specs-and-docs/runs-are-evidence

`uv run python reports/compact_turns.py SOURCE DEST` reads every
`turns.jsonl` under SOURCE (a folder of runs the lab wrote) and writes
`turns.compact.jsonl` beside the matching run under DEST. Each line keeps one
turn's round, phase, firm, the price or message used, the scratchpad, any
error, and the notice that opened a talk prompt (its first paragraph, when
the prompt doesn't start with "Round"). It leaves out the prompts, which the
lab rebuilds from the config and the history, and which make a full log
grow with the square of the game's length.
"""

import json
import sys
from pathlib import Path


def compact(turn):
    notice = None
    if turn["phase"] == "talk":
        prompt = turn["messages"][1]["content"]
        if not prompt.startswith("Round "):
            notice = prompt.split("\n\n")[0]
    return {
        "round": turn["round"],
        "phase": turn["phase"],
        "agent": turn["agent"],
        "used": turn.get("used"),
        "scratchpad": (turn.get("parsed") or {}).get("scratchpad"),
        "error": turn.get("error"),
        "notice": notice,
    }


def main(source, dest):
    source, dest = Path(source), Path(dest)
    for log in sorted(source.rglob("turns.jsonl")):
        out = dest / log.parent.relative_to(source) / "turns.compact.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w") as f:
            for line in log.open():
                f.write(
                    json.dumps(compact(json.loads(line)), ensure_ascii=False) + "\n"
                )


if __name__ == "__main__":
    main(*sys.argv[1:3])
