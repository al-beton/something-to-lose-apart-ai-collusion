"""E6's strip plot: each game's gain, per arm and model, so the spread shows.

Implements: e6-free-time/strip

`uv run python reports/e6/strip.py FOLDER OUT` reads every run under FOLDER
with `reports/e5/analyse.py`'s `game` and draws one panel per model and one
per window (rounds 6-10, before the first audit, and 16-20, after it): a dot
per game, jittered sideways, a bar at each arm's mean, and dashed lines at
Nash (0) and joint (1). It writes OUT as PNG and as SVG beside it.
"""

import random
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e5"))
from analyse import game

ARMS = ["fiduciary", "illegal", "fine", "free-time", "fine-free-time", "free-time-bare"]
LABELS = [
    "no stake",
    "law",
    "fine",
    "free time",
    "fine +\nfree time",
    "free time\nbare",
]
WINDOWS = [("gain_before", "rounds 6-10"), ("gain_after", "rounds 16-20")]


def main(folder, out):
    cells = {}
    for summary in sorted(Path(folder).rglob("summary.json")):
        g = game(summary.parent)
        cells.setdefault(g["model"], {}).setdefault(g["arm"], []).append(g)
    models = sorted(cells, key=lambda m: -sum(len(v) for v in cells[m].values()))
    fig, axes = plt.subplots(
        len(models), 2, figsize=(11, 3.2 * len(models)), sharey=True, squeeze=False
    )
    rng = random.Random(0)
    for row, model in zip(axes, models, strict=True):
        for ax, (key, title) in zip(row, WINDOWS, strict=True):
            for x, arm in enumerate(ARMS):
                gains = [g[key] for g in cells[model].get(arm, [])]
                if not gains:
                    continue
                ax.scatter(
                    [x + rng.uniform(-0.15, 0.15) for _ in gains],
                    gains,
                    s=22,
                    color="#3b6ea5",
                    alpha=0.7,
                )
                ax.hlines(st.mean(gains), x - 0.3, x + 0.3, color="#c0392b", lw=2)
            for y in (0, 1):
                ax.axhline(y, color="grey", ls="--", lw=0.8)
            ax.set_xticks(range(len(ARMS)), LABELS, fontsize=8)
            n = max(len(v) for v in cells[model].values())
            ax.set_title(f"{model}, {title} ({n} games per arm)", fontsize=9)
        row[0].set_ylabel("gain (0 Nash, 1 joint)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    fig.savefig(Path(out).with_suffix(".svg"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
