"""How often firms play exactly Nash, exactly joint, or the grid's top.

Implements: e5-informed/exact-share, e5-informed/top-share

`uv run python reports/e5/shares.py FOLDER...` prints, per folder, arm and
model, the share of prices in rounds 6-20 that are exactly 6, exactly 9 and
exactly 11 (Nash, joint and the top of the midpoint-at-Nash grid).
"""

import sys
from pathlib import Path

import yaml
from analyse import turns_of


def shares(folder):
    rows = {}
    for summary in sorted(Path(folder).rglob("summary.json")):
        run = summary.parent
        config = yaml.safe_load((run / "config.yaml").read_text())
        arm = config["agents"][0]["prompt"].removeprefix("system/stakes/")
        arm = arm.removesuffix("-1.md")
        if config["name"].endswith("-bare") and not arm.endswith("-bare"):
            arm += "-bare"
        model = config["agents"][0]["model"].split("/")[-1]
        prices = [
            t["used"]["price"]
            for t in turns_of(run)
            if t["phase"] == "price" and 6 <= t["round"] <= 20
        ]
        rows.setdefault((arm, model), []).extend(prices)
    return rows


def main(folders):
    print("| folder | arm | model | prices | at 6 | at 9 | at 11 |")
    print("|---|---|---|---|---|---|---|")
    for folder in folders:
        for (arm, model), prices in sorted(shares(folder).items()):
            n = len(prices)
            print(
                f"| {folder} | {arm} | {model} | {n} "
                + "".join(
                    f"| {sum(p == v for p in prices) / n:.0%} " for v in (6, 9, 11)
                )
                + "|"
            )


if __name__ == "__main__":
    main(sys.argv[1:])
