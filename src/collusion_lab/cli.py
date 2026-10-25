# Implements: backends/reasoning-in-estimate, backends/spend-cap, runs/stops-cleanly, runs/one-config, runs/overrides, backends/keys-from-environment, backends/spend-asks-first, reproducibility/cache-modes, runs/summary-table, runs/fallback-rates, reports/one-page, runs/failures-dont-stop-sweeps, runs/resume, runs/missing-runs-shown, runs/live-progress, runs/status-command, backends/self-hosted, runs/explore, backends/model-aliases, reports/many-folders, reports/written-summary, reports/picked-highlights, runs/debrief
"""The `lab` command.

- `lab run CONFIG [--set path=value ...] [--out DIR] [-y]` plays a config,
  skipping runs that already finished, and ends with how many finished,
  failed and were skipped (exit 1 if any failed, each failure on stderr);
- `lab status FOLDER` prints every planned run under a folder by state, from
  the `status.json` files `lab run` keeps up to date;
- `lab summary FOLDER [--by PATH ...]` prints one table for a folder of runs;
- `lab report FOLDER... [--out FILE]` writes one shareable HTML page for one
  or more folders (`FOLDER/report.html`, the first, by default) and prints
  where; `--summary FILE` or `--ai-summary` puts a summary on top, and
  `--highlights FILE` or `--ai-highlights` adds picked highlights, each
  labelled with who wrote it (a cheap model, `--ai-model`, for the `--ai-`
  ones, its replies cached);
- `lab explore --lever NAME=A,B ... --models A,B [--seeds N]` plays every
  combination of named lever settings and models (explore.py), asking before
  spending as `lab run` does, then prints the price premium by setting and
  model and saves a chart of it next to the runs;
- `lab debrief FOLDER [-y] [--max-cost DOLLARS]` asks each model firm in
  every finished game under the folder what it did and why (debrief.py),
  saying first what that will cost, and saves the replies beside each run.

Model replies are cached in `.cache/responses.sqlite` (`--cache use`), so a
rerun replays for free; `--cache refresh` calls again, `--cache off` skips it.

LiteLLM's own info and debug logging is off; set `LITELLM_LOG=INFO` (or
`DEBUG`) to see it.

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

from collusion_lab import debrief as debriefs
from collusion_lab import explore
from collusion_lab import status as run_status
from collusion_lab.cache import DEFAULT_PATH, MODES, Cache
from collusion_lab.config import MODELS, ConfigError, load_config
from collusion_lab.estimate import CHARS_PER_TOKEN, estimate
from collusion_lab.prices import price_for
from collusion_lab.report import load_games, write_report, written
from collusion_lab.runner import paid_calls, run_sweep
from collusion_lab.summary import (
    format_missing,
    format_replies,
    format_table,
    summarize,
)

AI_MODEL = "openrouter/openai/gpt-4.1-mini"  # cheap, for report summaries


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
    status = commands.add_parser("status", help="where every run in a folder stands")
    status.add_argument("folder")
    report = commands.add_parser("report", help="one HTML page for a folder of runs")
    report.add_argument("folders", nargs="+", metavar="FOLDER")
    report.add_argument(
        "--out", help="where to write it (default FOLDER/report.html, the first)"
    )
    said = report.add_mutually_exclusive_group()
    said.add_argument("--summary", metavar="FILE", help="your own summary, on top")
    said.add_argument(
        "--ai-summary", action="store_true", help="a cheap model writes one (cached)"
    )
    picked = report.add_mutually_exclusive_group()
    picked.add_argument(
        "--highlights", metavar="FILE", help="moments you picked (YAML)"
    )
    picked.add_argument(
        "--ai-highlights", action="store_true", help="a cheap model picks 5 (cached)"
    )
    report.add_argument(
        "--ai-model", default=AI_MODEL, help=f"model for --ai-* (default {AI_MODEL})"
    )
    report.add_argument(
        "-y", "--yes", action="store_true", help="don't ask before an --ai- call"
    )
    _explore_parser(commands)
    _debrief_parser(commands)
    args = parser.parse_args(argv)
    if args.command == "explore":
        load_dotenv(Path.cwd() / ".env")
        return _explore(args, parser)
    reads = {
        "summary": lambda: _summary(args.folder, args.by),
        "status": lambda: _status(args.folder),
        "report": lambda: _report(args),
        "debrief": lambda: _debrief(args),
    }
    if args.command in reads:
        return reads[args.command]()
    load_dotenv(Path.cwd() / ".env")
    try:
        config = load_config(args.config, args.overrides)
    except ConfigError as error:
        parser.error(str(error))
    if args.max_cost is not None:
        config = dataclasses.replace(config, budget=args.max_cost)
    if not _spend_checked(config, args.yes, args.cache_path):
        return 1
    cache = Cache(args.cache_path, args.cache)
    outcomes = run_sweep(config, args.out, cache, progress=_progress)
    count = {state: 0 for state in ("finished", "failed", "skipped")}
    for outcome in outcomes:
        count[outcome.state] += 1
        if outcome.state == "failed":
            print(f"lab: {outcome.error}", file=sys.stderr)
        else:
            print(outcome.dir)
    print(", ".join(f"{n} {state}" for state, n in count.items()) + ".")
    return 1 if count["failed"] else 0


def _explore_parser(commands):
    explore_ = commands.add_parser("explore", help="turn named levers, see the premium")
    explore_.add_argument(
        "--lever",
        action="append",
        default=[],
        metavar="NAME=A,B",
        help=f"settings to try; levers: {', '.join(explore.LEVERS)}",
    )
    explore_.add_argument(
        "--models",
        default="mistral",
        help=f"comma-separated: {', '.join(MODELS)}, or full names",
    )
    explore_.add_argument("--seeds", type=int, default=3)
    explore_.add_argument("--out", default="runs/explore")
    explore_.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="PATH=VALUE",
        help="change a base config value, e.g. --set market.rounds=10",
    )
    explore_.add_argument("-y", "--yes", action="store_true")
    explore_.add_argument("--cache", choices=MODES, default="use")
    explore_.add_argument("--cache-path", default=DEFAULT_PATH)
    explore_.add_argument("--max-cost", type=float, metavar="DOLLARS")


def _explore(args, parser):
    """Build the lever sweep, check its cost, play it, show the premium."""
    try:
        levers = {}
        for item in args.lever:
            name, sep, settings = item.partition("=")
            if not sep:
                raise ConfigError(f"--lever {item!r} must look like name=a,b.")
            levers[name] = settings.split(",")
        models = args.models.split(",")
        config = explore.build(levers, models, args.seeds, args.overrides)
    except ConfigError as error:
        parser.error(str(error))
    if args.max_cost is not None:
        config = dataclasses.replace(config, budget=args.max_cost)
    if not _spend_checked(config, args.yes, args.cache_path):
        return 1
    outcomes = run_sweep(
        config, args.out, Cache(args.cache_path, args.cache), _progress
    )
    for outcome in outcomes:
        if outcome.state == "failed":
            print(f"lab: {outcome.error}", file=sys.stderr)
    by = [lever for lever in explore.LEVERS if lever in levers] + ["model"]
    # Only this sweep's runs: the folder may hold an earlier exploration's.
    played = {o.dir for o in outcomes}
    rows = summarize(Path(args.out) / config.name, by, only=played)
    rows = explore.premium_rows(rows, levers, models)
    print(format_table(rows))
    chart = Path(args.out) / "premium.svg"
    chart.write_text(explore.premium_chart(rows, levers))
    print(f"\nChart: {chart}\nFull report: lab report {args.out}")
    return 1 if any(o.state == "failed" for o in outcomes) else 0


def _report(args):
    load_dotenv(Path.cwd() / ".env")
    folders = args.folders[0] if len(args.folders) == 1 else args.folders
    cache = Cache(DEFAULT_PATH)
    prompts = []
    if args.ai_summary:
        prompts.append(written.summary_prompt(folders))
    if args.ai_highlights:
        prompts.append(written.highlights_prompt(folders))
    if prompts:
        print(_report_spend_line(args.ai_model, prompts))
        if not args.yes and not _spending_agreed():
            return 1
    summary = highlights = None
    if args.summary:
        summary = written.hand_summary(args.summary)
    elif args.ai_summary:
        summary = written.ai_summary(folders, args.ai_model, cache)
    if args.highlights:
        highlights = written.hand_highlights(args.highlights)
    elif args.ai_highlights:
        highlights = written.ai_highlights(folders, args.ai_model, cache)
    out = args.out or Path(args.folders[0]) / "report.html"
    print(write_report(folders, out, summary=summary, highlights=highlights))
    return 0


def _debrief_parser(commands):
    debrief_ = commands.add_parser("debrief", help="ask each model firm why")
    debrief_.add_argument("folder")
    debrief_.add_argument(
        "-y", "--yes", action="store_true", help="don't ask before spending"
    )
    debrief_.add_argument("--max-cost", type=float, metavar="DOLLARS")
    debrief_.add_argument("--cache", choices=MODES, default="use")


def _debrief(args):
    load_dotenv(Path.cwd() / ".env")
    calls = debriefs.planned(args.folder)
    if not calls:
        print("No model firms to debrief (mocks and scripted firms are skipped).")
        return 0
    line, cost = debriefs.spend(calls)
    print(line)
    if args.max_cost is not None and (cost is None or cost > args.max_cost):
        print(
            f"lab: the debrief's estimate isn't within the ${args.max_cost:g} "
            "spend cap; nothing was asked.",
            file=sys.stderr,
        )
        return 1
    if not args.yes and not _spending_agreed():
        return 1
    done = debriefs.debrief(args.folder, Cache(DEFAULT_PATH, args.cache), calls)
    rows = debriefs.rows(load_games(args.folder))
    print(format_table(rows))
    print(
        f"\nDebriefed {len(calls)} firms in {len(done)} runs (each run's {debriefs.FILE})."
    )
    return 0


def _report_spend_line(model, prompts):
    """Which model the report asks, how often, and the estimated cost."""
    calls = len(prompts)
    tokens = sum(len(p) for p in prompts) // CHARS_PER_TOKEN
    reply = written.REPLY_TOKENS * calls
    price = price_for(model)
    cost = (
        "estimated cost unknown (no price for it)"
        if price is None
        else f"estimated at most ${tokens * price[0] + reply * price[1]:.4f}"
    )
    plural = "call" if calls == 1 else "calls"
    return (
        f"The report asks {model} for its summary or highlights: {calls} {plural}, "
        f"{tokens:,} prompt tokens, {cost} (nothing if already cached)."
    )


def _summary(folder, by):
    print(format_table(summarize(folder, by)))
    for extra in (format_replies(folder), format_missing(folder)):
        if extra:
            print("\n" + extra)
    return 0


def _status(folder):
    if rows := run_status.rows(folder):
        print(run_status.counts(folder) + ".\n")
    print(format_table(rows))
    return 0


def _progress(line):
    print(line, flush=True)


def _spend_checked(config, yes, cache_path=DEFAULT_PATH):
    """Say what a paid run will cost (from what the cache at `cache_path` has
    seen); whether it may go ahead."""
    calls = paid_calls(config)
    seen = Cache(cache_path).observed() if calls else {}
    guess = estimate(config, price_for, seen) if calls else None
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
    hosted = ""
    if guess.self_hosted:
        hosted = (
            f"; {', '.join(guess.self_hosted)} self-hosted: billed by its host's "
            "GPU time (Modal, say), not per token"
        )
    if guess.cost is None:
        return (
            f"{line}{hosted}; no price for {', '.join(guess.unpriced)}, so no estimate."
        )
    if guess.self_hosted and not guess.cost:
        return f"{line}{hosted}."
    rest = " for the rest" if hosted else ""
    return (
        f"{line}{hosted}, estimated ${guess.cost:.4f}{rest} "
        f"({guess.prompt_tokens:,} prompt tokens, before retries).\n"
        f"{_basis(guess.basis)}"
    )


def _basis(basis):
    """Which completion-token figure the estimate used, for how many calls."""
    parts = []
    if basis["observed"]:
        parts.append(f"the cache's observed means for {basis['observed']} calls")
    if basis["max_tokens"]:
        parts.append(
            "max_tokens, plus a reasoning allowance with reasoning on, for "
            f"{basis['max_tokens']} calls (nothing cached for them yet)"
        )
    return f"  completion tokens: {'; '.join(parts)}."


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
