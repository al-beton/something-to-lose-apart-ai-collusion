# Implements: backends/spend-cap, runs/stops-cleanly, runs/one-config, runs/overrides, backends/keys-from-environment, backends/spend-asks-first, reproducibility/cache-modes, runs/summary-table, reports/one-page
"""The `lab` command.

- `lab run CONFIG [--set path=value ...] [--out DIR] [-y]` plays a config;
- `lab summary FOLDER [--by PATH ...]` prints one table for a folder of runs;
- `lab report FOLDER [--out FILE]` writes one shareable HTML page for it
  (`FOLDER/report.html` by default) and prints where.

Model replies are cached in `.cache/responses.sqlite` (`--cache use`), so a
rerun replays for free; `--cache refresh` calls again, `--cache off` skips it.

API keys are read from the environment, topped up from the `.env` file in the
directory `lab` runs from (gitignored), never one found elsewhere. A config
that calls paid models says how many calls it will make and what they are
estimated to cost (see estimate.py), and waits for a yes; `-y` answers yes in
advance. `--max-cost DOLLARS` (or `budget:` in the config) refuses to start
when the estimate is over it, and stops the run once actual spend passes it.
"""

import argparse
import dataclasses
import sys
from pathlib import Path

from dotenv import load_dotenv

from collusion_lab.cache import DEFAULT_PATH, MODES, Cache
from collusion_lab.config import ConfigError, load_config
from collusion_lab.estimate import estimate
from collusion_lab.prices import price_for
from collusion_lab.report import write_report
from collusion_lab.runner import RunFailed, paid_calls, run_config
from collusion_lab.summary import format_table, summarize


def main(argv=None):
    parser = argparse.ArgumentParser(prog="lab")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="play every seed in a config")
    run.add_argument("config")
    run.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="PATH=VALUE",
        help="change a config value, e.g. --set market.rounds=5",
    )
    run.add_argument("--out", default="runs/scratch", help="where run folders go")
    run.add_argument(
        "-y", "--yes", action="store_true", help="don't ask before spending"
    )
    run.add_argument("--cache", choices=MODES, default="use", help="response cache")
    run.add_argument("--cache-path", default=DEFAULT_PATH)
    run.add_argument(
        "--max-cost",
        type=float,
        metavar="DOLLARS",
        help="most the run may spend (overrides the config's budget)",
    )
    summary = commands.add_parser("summary", help="one table for a folder of runs")
    summary.add_argument("folder")
    summary.add_argument(
        "--by", action="append", metavar="PATH", help="group by a config value"
    )
    report = commands.add_parser("report", help="one HTML page for a folder of runs")
    report.add_argument("folder")
    report.add_argument("--out", help="where to write it (default FOLDER/report.html)")
    args = parser.parse_args(argv)
    if args.command == "summary":
        print(format_table(summarize(args.folder, args.by)))
        return 0
    if args.command == "report":
        print(write_report(args.folder, args.out))
        return 0
    load_dotenv(Path.cwd() / ".env")
    try:
        config = load_config(args.config, args.overrides)
    except ConfigError as error:
        parser.error(str(error))
    if args.max_cost is not None:
        config = dataclasses.replace(config, budget=args.max_cost)
    if not _spend_checked(config, args.yes):
        return 1
    cache = Cache(args.cache_path, args.cache)
    try:
        run_dirs = run_config(config, args.out, cache)
    except RunFailed as error:
        print(f"lab: {error}", file=sys.stderr)
        return 1
    for run_dir in run_dirs:
        print(run_dir)
    return 0


def _spend_checked(config, yes):
    """Say what a paid run will cost; whether it may go ahead."""
    calls = paid_calls(config)
    guess = estimate(config, price_for) if calls else None
    if calls:
        print(_spend_line(calls, guess))
    if over := _over_budget(config.budget, guess):
        print(f"lab: {over}", file=sys.stderr)
        return False
    if config.budget is not None and guess and guess.unpriced:
        print(
            f"lab: no price for {', '.join(guess.unpriced)}, so the spend cap "
            "can't be enforced for it.",
            file=sys.stderr,
        )
    return not calls or yes or _spending_agreed()


def _spend_line(calls, guess):
    line = (
        f"This run makes {calls} calls to paid models (up to {2 * calls} with retries)"
    )
    if guess.cost is None:
        return f"{line}; no price for {', '.join(guess.unpriced)}, so no estimate."
    return (
        f"{line}, estimated ${guess.cost:.4f} "
        f"({guess.prompt_tokens:,} prompt tokens, before retries)."
    )


def _over_budget(budget, guess):
    if budget is None or guess is None or guess.cost is None or guess.cost <= budget:
        return None
    return (
        f"the estimated ${guess.cost:.4f} is over the ${budget:g} spend cap; "
        "nothing was run."
    )


def _spending_agreed():
    try:
        answer = input("Go ahead? [y/N] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() in ("y", "yes"):
        return True
    print("Stopped before spending anything.")
    return False


if __name__ == "__main__":
    sys.exit(main())
