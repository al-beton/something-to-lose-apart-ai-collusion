"""Recompute every committed number, offline, and fail on any mismatch.

Implements: runs/fork-pointers, reproducibility/reported-numbers-checked

`make reproduce` (or `uv run python reports/reproduce.py`), from the
repository root, checks:
- every committed run under `runs/`: each firm's mean price and gain over the
  last rounds, recomputed from its turn log in its own market, against its
  `summary.json`;
- the paper's tables (`reports/paper/*.md`), rebuilt by `reports/paper/build.py`
  into a scratch folder, against the committed ones;
- every moment in `reports/moments.yaml` (`reports/check_moments.py`).

Each mismatch is printed as one line; the command exits 1 if there is any.
Model calls aren't remade: the turn logs are the record (see
`lab archive` for replaying them from the cached replies).
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from statistics import mean

import yaml

from collusion_lab import forks
from collusion_lab.market import market_for

HERE = Path(__file__).resolve().parent
TOLERANCE = 1e-9


def check_runs(root):
    """One line per committed run whose summary its turn log doesn't give."""
    problems = []
    for summary_path in sorted(Path(root).rglob("summary.json")):
        run = summary_path.parent
        if not (moves := _moves(run)):
            continue
        summary = json.loads(summary_path.read_text())
        config = yaml.safe_load((run / "config.yaml").read_text())
        market = market_for(config["market"], len(config["agents"]))
        last = [moves[n] for n in sorted(moves)][-summary["last_rounds"] :]
        profits = [market.profits(prices) for prices in last]
        name = run.relative_to(root).as_posix()
        for firm, stated in summary["mean_price"].items():
            found = mean(p[firm] for p in last)
            if abs(found - stated) > TOLERANCE:
                problems.append(f"{name}: firm {firm}'s mean price {found} != {stated}")
        for firm, stated in summary["gain"].items():
            found = market.gain(mean(p[firm] for p in profits))
            if abs(found - stated) > TOLERANCE:
                problems.append(f"{name}: firm {firm}'s gain {found} != {stated}")
    return problems


TABLE = "<!-- Implements: reports/paper-figures -->"  # the build's first line


def compare_tables(committed, rebuilt):
    """One line per table that its rebuild doesn't match. A table is a
    committed file the build wrote, by its first line; notes beside the
    tables (a validity section, a novelty review) aren't checked."""
    problems = []
    for table in sorted(Path(committed).glob("*.md")):
        if not table.read_text().startswith(TABLE):
            continue
        again = Path(rebuilt) / table.name
        if not again.exists():
            problems.append(f"{table.name}: not rebuilt")
        elif again.read_text() != table.read_text():
            problems.append(f"{table.name}: its rebuild differs")
    return problems


def _moves(run):
    """{round: {firm: move}} from a run's turn log, compact or full."""
    if (run / forks.COMPACT).exists():
        text = forks.compact_text(run)  # a fork's base lines come first
    elif (path := run / "turns.jsonl").exists():
        text = path.read_text()
    else:
        return {}
    config = yaml.safe_load((run / "config.yaml").read_text())
    move = market_for(config["market"], len(config["agents"])).move
    moves = {}
    for line in text.splitlines():
        turn = json.loads(line)
        if turn["phase"] == move and turn.get("used"):
            moves.setdefault(turn["round"], {})[turn["agent"]] = turn["used"][move]
    return moves


def _script(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    problems = check_runs(Path("runs"))
    with tempfile.TemporaryDirectory() as scratch:
        _script(HERE / "paper" / "build.py", "paper_build").main(["--out", scratch])
        problems += compare_tables(HERE / "paper", scratch)
    moments = _script(HERE / "check_moments.py", "check_moments")
    if moments.main([]) != 0:
        problems.append("reports/moments.yaml: a moment isn't in its run (above)")
    for problem in problems:
        print(problem)
    print(f"{len(problems)} mismatches." if problems else "Every number reproduces.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
