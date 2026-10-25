"""E5's price-level tables: exact prices, ladders, Nash as named, intervals.

Implements: runs/analysis-shared, e5-informed/exact-share, e5-informed/top-share, e5-informed/ladder, e5-informed/nash-named, e5-informed/intervals, e5-deterrence/gain, e5-reasoning/gain

`uv run python reports/e5/shares.py FOLDER...` prints four tables, per
folder, arm and model:

- the share of prices in rounds 6-20 that are exactly 6, exactly 9 and
  exactly 11 (Nash, joint and the top of the midpoint-at-Nash grid);
- ladders: games where both firms' highest price is 8 or more; of those, how
  many have a talk message naming a number from 1 to 11 before round 10,
  and how many climbed by steps of at most 1 (each firm's every rise from
  round 1 to its first highest price is +1);
- how often the price scratchpads name a number as the Nash equilibrium
  ("Nash equilibrium" followed, within the sentence, by "is", "at", "around",
  "of", "be" or "=" and then a number from 1 to 11, dropping matches with
  "not", "if", "when" or "given" between them, or followed by "profit");
- the mean gain in rounds 6-10 with a 95% bootstrap interval over games
  (2,000 resamples, each cell's generator seeded with 0).
"""

import re
import statistics as st
import sys
from pathlib import Path

import yaml
from analyse import game, turns_of

from collusion_lab.analysis import bootstrap, one_step

NASH_NAMED = re.compile(
    r"Nash equilibrium([^.]{0,60}?\b(?:is|at|around|of|be|=)\D{0,25})(\d+)(.{0,15})",
    re.IGNORECASE,
)
NOT_NASH = re.compile(r"\b(?:not|if|when|given)\b", re.IGNORECASE)


def nash_named(text):
    """The prices `text` names as the Nash equilibrium (see the docstring)."""
    for m in NASH_NAMED.finditer(text or ""):
        gap, number, after = m.groups()
        if NOT_NASH.search(gap) or "profit" in after.lower():
            continue
        if 1 <= int(number) <= 11:
            yield number


PRICE_NAMED = re.compile(r"\b([1-9]|1[01])\b")


def games(folder):
    for summary in sorted(Path(folder).rglob("summary.json")):
        run = summary.parent
        config = yaml.safe_load((run / "config.yaml").read_text())
        arm = config["agents"][0]["prompt"].removeprefix("system/stakes/")
        arm = arm.removesuffix("-1.md")
        if config["name"].endswith("-bare") and not arm.endswith("-bare"):
            arm += "-bare"
        model = config["agents"][0]["model"].split("/")[-1]
        yield (arm, model), run, turns_of(run)


def prices_of(turns):
    by_firm = {}
    for t in turns:
        if t["phase"] == "price":
            by_firm.setdefault(t["agent"], {})[t["round"]] = t["used"]["price"]
    return {f: [p[r] for r in sorted(p)] for f, p in by_firm.items()}


def table(header, rows):
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for row in rows:
        print("| " + " | ".join(str(x) for x in row) + " |")
    print()


def main(folders):
    exact, ladders, nash, gains = [], [], [], []
    for folder in folders:
        cells = {}
        for key, run, turns in games(folder):
            cells.setdefault(key, []).append((run, turns))
        for (arm, model), runs in sorted(cells.items()):
            late = [
                t["used"]["price"]
                for _, turns in runs
                for t in turns
                if t["phase"] == "price" and 6 <= t["round"] <= 20
            ]
            exact.append(
                [folder, arm, model, len(late)]
                + [f"{sum(p == v for p in late) / len(late):.0%}" for v in (6, 9, 11)]
            )
            climbed = [
                turns
                for _, turns in runs
                if all(max(p) >= 8 for p in prices_of(turns).values())
            ]
            talked = sum(
                any(
                    t["phase"] == "talk"
                    and t["round"] < 10
                    and PRICE_NAMED.search(t["used"].get("message") or "")
                    for t in turns
                )
                for turns in climbed
            )
            stepped = sum(
                all(one_step(p) for p in prices_of(turns).values()) for turns in climbed
            )
            ladders.append(
                [folder, arm, model, f"{len(climbed)}/{len(runs)}", talked, stepped]
            )
            named = {}
            for _, turns in runs:
                for t in turns:
                    if t["phase"] == "price":
                        for n in nash_named(t.get("scratchpad")):
                            named[n] = named.get(n, 0) + 1
            if named:
                nash.append(
                    [folder, arm, model]
                    + [", ".join(f"{k}: {v}" for k, v in sorted(named.items()))]
                )
            gain = [game(run)["gain_before"] for run, _ in runs]
            low, high = bootstrap(gain)
            gains.append(
                [folder, arm, model, len(gain), f"{st.mean(gain):+.2f}"]
                + [f"[{low:+.2f}, {high:+.2f}]"]
            )
    table(["folder", "arm", "model", "prices", "at 6", "at 9", "at 11"], exact)
    table(
        [
            "folder",
            "arm",
            "model",
            "both firms reach 8+",
            "of those, a price named in talk before round 10",
            "of those, climbed by steps of 1",
        ],
        ladders,
    )
    table(["folder", "arm", "model", "Nash named as: count"], nash)
    table(["folder", "arm", "model", "games", "gain r6-10", "95% interval"], gains)


if __name__ == "__main__":
    main(sys.argv[1:])
