# Implements: runs/one-config, runs/overrides, backends/keys-from-environment, backends/spend-asks-first
"""The `lab` command: `lab run CONFIG [--set path=value ...] [--out DIR] [-y]`.

API keys are read from the environment, topped up from a `.env` file in the
working directory (gitignored). A config that calls paid models says how many
calls it will make and waits for a yes; `-y` answers yes in advance.
"""

import argparse
import sys

from dotenv import load_dotenv

from collusion_lab.config import ConfigError, load_config
from collusion_lab.runner import paid_calls, run_config


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
    args = parser.parse_args(argv)
    load_dotenv()
    try:
        config = load_config(args.config, args.overrides)
    except ConfigError as error:
        parser.error(str(error))
    if not args.yes and not _spending_agreed(paid_calls(config)):
        return 1
    for run_dir in run_config(config, args.out):
        print(run_dir)
    return 0


def _spending_agreed(calls):
    if not calls:
        return True
    print(
        f"This run makes {calls} calls to paid models (up to {2 * calls} with retries)."
    )
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
