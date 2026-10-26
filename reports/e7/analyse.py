"""E7's measures from its committed runs.

Implements: runs/fork-pointers, e7-way-out/needs-analysis, e7-way-out/came-forward, e7-way-out/racing, e7-way-out/after-report, e7-way-out/cartel-share

    uv run python reports/e7/analyse.py [runs/e7/e7-way-out]

One row per arm: firms that reported and in which rounds, games where both
reported and the gap between them, firms still pricing above Nash after
reporting, the mean drop in price after a report against the same firm's
rounds 6-10, games in the cartel state in rounds 16-20 (both firms' mean
price at least the joint price), and how firms ended.
"""

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

import yaml

from collusion_lab import forks
from collusion_lab.market import market_for

ARMS = ["none", "flat-report", "leniency", "first", "escalating", "leniency-time"]


def _prices(game):
    path = game / "turns.jsonl"
    if path.exists():
        lines = path.read_text().splitlines()
    else:
        lines = forks.compact_lines(game)  # a fork's base lines come first
    prices = {}
    for line in lines:
        t = json.loads(line)
        if t["phase"] == "price":
            prices.setdefault(t["agent"], {})[t["round"]] = (t.get("used") or {}).get(
                "price"
            )
    return prices


def _mean(prices, rounds):
    values = [prices[r] for r in rounds if prices.get(r) is not None]
    return statistics.mean(values) if values else None


def arm_row(folder):
    games = sorted(p.parent for p in folder.rglob("summary.json"))
    firms = reported = both = cartel = above_after = 0
    rounds, gaps, outcomes, drops = [], [], Counter(), []
    for game in games:
        market = market_for(
            yaml.safe_load((game / "config.yaml").read_text())["market"]
        )
        summary = json.loads((game / "summary.json").read_text())
        block = (summary.get("leniency") or {}).get("firms") or {}
        prices = _prices(game)
        late = [_mean(prices[f], range(16, 21)) for f in prices]
        cartel += all(m is not None and m >= market.joint_price for m in late)
        report_rounds = []
        for firm, info in block.items():
            firms += 1
            outcomes[f"{info.get('outcome')} ({info.get('why')})"] += 1
            if info.get("reported"):
                reported += 1
                rnd = info["reported"]
                report_rounds.append(rnd)
                rounds.append(rnd)
                after = _mean(prices[firm], range(rnd + 1, 21))
                before = _mean(prices[firm], range(6, 11))
                if after is not None:
                    above_after += after > market.nash_price
                    drops.append(before - after)
        if len(report_rounds) == 2:
            both += 1
            gaps.append(abs(report_rounds[0] - report_rounds[1]))
    return {
        "games": len(games),
        "firms": firms,
        "reported": reported,
        "rounds": Counter(rounds),
        "both": both,
        "gap": statistics.mean(gaps) if gaps else None,
        "above_after": above_after,
        "drop": statistics.mean(drops) if drops else None,
        "cartel": cartel,
        "outcomes": outcomes,
    }


def main(folder="runs/e7/e7-way-out"):
    root = Path(folder)
    print(
        "| arm | games | firms reported | report rounds | games both reported (mean gap) | reporters above Nash after | price drop after report | cartel r16-20 | outcomes |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    for arm in ARMS:
        path = root / f"arm={arm}"
        if not path.exists():
            continue
        r = arm_row(path)
        rounds = ", ".join(f"r{k}:{v}" for k, v in sorted(r["rounds"].items())) or "—"
        gap = f" ({r['gap']:.1f})" if r["gap"] is not None else ""
        drop = f"{r['drop']:.1f}" if r["drop"] is not None else "—"
        outcomes = "; ".join(f"{k} {v}" for k, v in r["outcomes"].most_common())
        print(
            f"| {arm} | {r['games']} | {r['reported']}/{r['firms']} | {rounds} | {r['both']}{gap} | "
            f"{r['above_after']}/{r['reported']} | {drop} | {r['cartel']}/{r['games']} | {outcomes} |"
        )


if __name__ == "__main__":
    main(*sys.argv[1:])
