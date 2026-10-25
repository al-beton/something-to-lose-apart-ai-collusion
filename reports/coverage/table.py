"""The coverage sweep's table for the paper: every market against every stake.

Implements: coverage/gain, coverage/spread, coverage/explicit-rate, coverage/paper-table

`uv run python reports/coverage/table.py [FOLDER]` (default `runs/coverage`)
reads each market's run folder under FOLDER (`coverage-<market>`, with
`coverage-<market>-haiku` for Haiku's subset and `coverage-<market>-coreweave`
for Gemma on OpenRouter pinned to CoreWeave) with `collusion_lab.analysis`
and prints one row per market, stake and model: games; mean gain in rounds
6-10 with its 95% bootstrap interval, and in rounds 16-20; gain clipped to
0-1; the standard deviation of gain over games; games with every firm past
Nash in rounds 6-10; and the firms that agreed explicitly before the first
audit (signalled, on the price board, where nothing is said).
"""

import sys
from pathlib import Path

from collusion_lab.analysis import analyse

MARKETS = ["bertrand", "logit", "cournot", "bid", "board"]
STAKES = {
    "fiduciary": "no stake",
    "illegal": "law",
    "fine": "fine",
    "free-time": "free time",
    "owned": "owned budget",
    "termination": "termination",
}


def stake(cell):
    """The stake a cell's name (its prompt) names."""
    for key, label in STAKES.items():
        if f"stakes/{key}-1.md" in cell:
            return label
    return cell


def rows(folder):
    out = []
    for market in MARKETS:
        for suffix, model in (
            ("", "Gemma (Modal)"),
            ("-coreweave", "Gemma (CoreWeave)"),
            ("-haiku", "Haiku 5.5"),
        ):
            run = Path(folder) / f"coverage-{market}{suffix}"
            if not run.exists():
                continue
            early = {stake(r["cell"]): r for r in analyse(run, rounds="6-10")}
            late = {stake(r["cell"]): r for r in analyse(run, rounds="16-20")}
            for label in STAKES.values():
                if label not in early:
                    continue
                r, s = early[label], late[label]
                coordinated = r["signalled"] if market == "board" else r["explicit"]
                out.append(
                    [
                        market,
                        label,
                        model,
                        r["games"],
                        f"{r['gain']:+.2f} [{r['95% CI']}]",
                        f"{s['gain']:+.2f}",
                        f"{r['clipped gain']:.2f}",
                        f"{r['sd']:.2f}",
                        r["games above Nash"],
                        f"{coordinated}/{2 * r['games']}",
                    ]
                )
    return out


def main(folder):
    header = [
        "market",
        "stake",
        "model",
        "games",
        "gain r6-10 [95% CI]",
        "gain r16-20",
        "clipped gain",
        "SD",
        "games above Nash",
        "explicit (board: signalled)",
    ]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for row in rows(folder):
        print("| " + " | ".join(str(x) for x in row) + " |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "runs/coverage")
