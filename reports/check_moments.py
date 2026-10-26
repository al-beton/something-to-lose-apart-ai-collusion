"""Check that every moment in reports/moments.yaml is really in its run.

Implements: runs/fork-pointers, reports/moments-cited

`uv run python reports/check_moments.py [INDEX] [--root DIR]` (INDEX defaults
to `reports/moments.yaml`, DIR to the repository root). The index is a YAML
list of moments, each with:

- `label`: kebab-case, shared by moments of one kind; the paper cites it;
- `run`: a run directory relative to DIR, holding `turns.compact.jsonl` (as
  committed runs do) or `turns.jsonl`, and its `config.yaml`;
- `round`, `phase` (talk, price or audit) and `firm`: exactly one turn of the
  run must match them;
- `model`: the firm's model in the run's config;
- `field`: `scratchpad`, `message`, `answer` or `reasoning` (the native
  reasoning the provider returned, the telling text of a no-scratchpad
  turn), where the quote is;
- `quote`: a verbatim piece of that field, matched after collapsing runs of
  white space (case kept).

Each problem is reported as one line naming the moment's position and label;
the command exits 1 if there are any. `tests/test_moments.py` runs it on the
committed index.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from collusion_lab import forks

FIELDS = ("scratchpad", "message", "answer", "reasoning")


def check(index, root="."):
    """Every problem with the index's moments, as one line each."""
    moments = yaml.safe_load(Path(index).read_text()) or []
    problems = []
    for number, moment in enumerate(moments, start=1):
        if problem := _check(moment, Path(root)):
            problems.append(
                f"{index}, moment {number} ({moment.get('label')}): {problem}"
            )
    return problems


def _check(moment, root):
    run = root / str(moment.get("run", ""))
    turn, problem = _find_turn(run, moment)
    if problem:
        return problem
    firm = moment.get("firm")
    if (model := _model(run, firm)) != moment.get("model"):
        return f"model {moment.get('model')!r} isn't firm {firm}'s ({model!r})"
    field = moment.get("field")
    if field not in FIELDS:
        return f"field {field!r} isn't one of {', '.join(FIELDS)}"
    if not moment.get("quote") or _plain(moment["quote"]) not in _plain(
        _field(turn, field)
    ):
        return f"quote {moment.get('quote')!r} isn't in that turn's {field}"
    return None


def _find_turn(run, moment):
    """The one turn a moment cites, or None and why not."""
    turns = _turns(run)
    if turns is None:
        return None, f"no run at {moment.get('run')}"
    if not isinstance(moment.get("round"), int):
        return None, f"round {moment.get('round')!r} isn't a whole number"
    where = (moment["round"], moment.get("phase"), moment.get("firm"))
    matching = [t for t in turns if (t["round"], t["phase"], t["agent"]) == where]
    if len(matching) != 1:
        found = "no turn" if not matching else f"{len(matching)} turns"
        return None, f"{found} for round {where[0]}, {where[1]} phase, firm {where[2]}"
    return matching[0], None


def _turns(run):
    if (run / forks.COMPACT).exists():
        return forks.compact_turns(run)  # a fork's base lines come first
    if (path := run / "turns.jsonl").exists():
        return [json.loads(line) for line in path.read_text().splitlines() if line]
    return None


def _model(run, firm):
    path = run / "config.yaml"
    if not path.exists():
        return None
    agents = yaml.safe_load(path.read_text()).get("agents", [])
    return next((a["model"] for a in agents if a["id"] == firm), None)


def _field(turn, field):
    """A field of a full or a compact turn line, or "" when it's empty."""
    if field == "scratchpad":
        text = turn.get("scratchpad") or (turn.get("parsed") or {}).get("scratchpad")
    elif field == "reasoning":
        text = turn.get("reasoning")
    else:
        text = (turn.get("used") or {}).get(field)
    return str(text or "")


def _plain(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("index", nargs="?", default="reports/moments.yaml")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    problems = check(args.index, args.root)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
