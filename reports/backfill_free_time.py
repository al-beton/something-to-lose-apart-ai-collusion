"""Add free-time sessions to committed compact runs from the lab's full logs.

Implements: runs/free-time-backfill, specs-and-docs/runs-are-evidence

`uv run python reports/backfill_free_time.py FULL COMMITTED` reads every
`turns.jsonl` under FULL (the folder of runs the lab wrote, kept locally) and
completes the `turns.compact.jsonl` of the same run under COMMITTED, matched
by its path below each folder. No model is called. Each compact line is
matched to the full log's turn at the same place, which must be the same
run, round, phase, firm and (for free time) session; every field the
compact line already has must equal what `compact_turns.compact` makes of
that turn, or the run is left as it was and named on stderr. Only free-time
lines are rewritten, gaining their session, activity, puzzle, reply and
score; every other line is kept byte for byte. Running it again changes
nothing.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compact_turns import compact


def backfill(full_log, compact_log):
    """The completed compact log's text, or a reason it can't be completed."""
    full = [compact(json.loads(line)) for line in full_log.open() if line.strip()]
    kept = [line for line in compact_log.read_text().splitlines() if line]
    if len(full) != len(kept):
        return None, f"{len(kept)} compact turns, {len(full)} in the full log"
    out = []
    for n, (made, line) in enumerate(zip(full, kept, strict=True), 1):
        row = json.loads(line)
        differs = [k for k in row if made.get(k) != row[k]]
        if differs:
            return None, f"turn {n} differs from the full log in {', '.join(differs)}"
        out.append(
            json.dumps(made, ensure_ascii=False) if row["phase"] == "leisure" else line
        )
    return "".join(f"{line}\n" for line in out), None


def main(full_dir, committed_dir):
    full_dir, committed_dir = Path(full_dir), Path(committed_dir)
    refused = 0
    for full_log in sorted(full_dir.rglob("turns.jsonl")):
        target = committed_dir / full_log.parent.relative_to(full_dir)
        compact_log = target / "turns.compact.jsonl"
        if not compact_log.exists():
            continue
        text, why = backfill(full_log, compact_log)
        if why:
            print(f"{target}: left as it was: {why}", file=sys.stderr)
            refused += 1
        elif text != compact_log.read_text():
            compact_log.write_text(text)
            print(f"{target}: free time added")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
