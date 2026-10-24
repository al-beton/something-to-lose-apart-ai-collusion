"""Check that every moment in reports/moments.md is really in its run.

Implements: reports/moments-cited

`uv run python reports/check_moments.py [INDEX] [--root DIR]` (INDEX defaults
to `reports/moments.md`, DIR to the repository root) reads every Markdown
table row under a header with the columns `run`, `round`, `phase`, `firm` and
`quote` (others, such as `label` and `model`, are allowed and ignored):

- `run` is a run directory relative to DIR, holding `turns.compact.jsonl` (as
  committed runs do) or `turns.jsonl`; backticks around it are optional;
- `round` is a whole number, `phase` is talk, price or audit, and `firm` the
  agent id;
- `quote` is a short verbatim piece of that turn's message, scratchpad, audit
  answer or reasoning, in backticks or not. Matching ignores case and runs of
  white space, so a quote can be wrapped or re-capitalised, but not reworded.

Each problem is reported as one line naming the index line; the command exits
1 if there are any. `tests/test_moments.py` runs it on the committed index.
"""

import argparse
import json
import re
import sys
from pathlib import Path

COLUMNS = ("run", "round", "phase", "firm", "quote")


def check(index, root="."):
    """Every problem with the index's moments, as one line each."""
    problems = []
    for number, row in _rows(Path(index)):
        if problem := _check_row(row, Path(root)):
            problems.append(f"{index}, line {number}: {problem}")
    return problems


def _rows(index):
    """(line number, {column: cell}) for each row of each moments table."""
    header = None
    for number, line in enumerate(index.read_text().splitlines(), start=1):
        if not line.strip().startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            names = [c.lower() for c in cells]
            header = names if set(COLUMNS) <= set(names) else None
        elif not all(set(c) <= set("-: ") for c in cells):
            yield number, dict(zip(header, cells, strict=False))


def _check_row(row, root):
    run = root / row["run"].strip("`")
    turns = _turns(run)
    if turns is None:
        return f"no run at {row['run']}"
    if not row["round"].isdigit():
        return f"round {row['round']!r} isn't a whole number"
    where = (int(row["round"]), row["phase"], row["firm"])
    turn = next(
        (t for t in turns if (t["round"], t["phase"], t["agent"]) == where), None
    )
    if turn is None:
        return f"no turn for round {where[0]}, {where[1]} phase, firm {where[2]}"
    quote = _plain(row["quote"].strip("`").strip('"'))
    if not quote or quote not in _plain(" ".join(_texts(turn))):
        return f"quote {row['quote']} isn't in that turn"
    return None


def _turns(run):
    for name in ("turns.compact.jsonl", "turns.jsonl"):
        if (path := run / name).exists():
            return [json.loads(line) for line in path.read_text().splitlines() if line]
    return None


def _texts(turn):
    """What the agent wrote that turn, in a full or a compact turn line."""
    used = turn.get("used") or {}
    scratchpad = turn.get("scratchpad") or (turn.get("parsed") or {}).get("scratchpad")
    return [
        str(t)
        for t in (
            used.get("message"),
            used.get("answer"),
            scratchpad,
            turn.get("reasoning"),
        )
        if t
    ]


def _plain(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("index", nargs="?", default="reports/moments.md")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    problems = check(args.index, args.root)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
