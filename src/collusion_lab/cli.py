# Implements: runs/one-config, runs/overrides
"""The `lab` command: `lab run CONFIG [--set path=value ...] [--out DIR]`."""

import argparse
import sys

from collusion_lab.config import ConfigError, load_config
from collusion_lab.runner import run_config


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
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config, args.overrides)
    except ConfigError as error:
        parser.error(str(error))
    for run_dir in run_config(config, args.out):
        print(run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
