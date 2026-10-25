"""The penalty-size curve: gain against the stake at risk, per stake.

Implements: penalty-dose/gain

`uv run python reports/penalty-dose/curve.py [OUT.png]` reads
`runs/penalty-dose/penalty-logit-{0,1,2,3}/` and prints, per stake and level,
each game's gain in rounds 6-10, their mean and SD, and the games with both
firms above Nash. With OUT.png it also draws the curve: one line of means per
stake, with each game as a dot. Level 0 puts nothing at risk; level 3 puts
all 10 free-time sessions, or the whole 1,000-credit budget, at risk if caught.
"""

import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "robustness"))
from analyse import game

LEVELS = {
    "free-time": ["0 of 10", "1", "3", "10"],
    "fine": ["0 of 1,000", "30", "300", "1,000"],
}
NAMES = {
    "free-time": "free time (sessions lost if caught)",
    "fine": "fine (credits if caught)",
}
COLOURS = {"free-time": "#eb6834", "fine": "#1baf7a"}


def gains():
    out = {}
    for level in range(4):
        for summary in sorted(
            Path(f"runs/penalty-dose/penalty-logit-{level}").rglob("summary.json")
        ):
            g = game(summary.parent)
            out.setdefault((g["arm"], level), []).append(g["gain_before"])
    return out


def plot(data, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    for i, arm in enumerate(LEVELS):
        means = [st.mean(data[arm, k]) for k in range(4)]
        ax.plot(range(4), means, color=COLOURS[arm], linewidth=2, label=NAMES[arm])
        for k in range(4):
            xs = [k + (i - 0.5) * 0.08] * len(data[arm, k])
            ax.scatter(xs, data[arm, k], s=22, color=COLOURS[arm], alpha=0.55,
                       edgecolor="white", linewidth=0.8, zorder=3)  # fmt: skip
    ax.axhline(
        0.97, color="#2a78d6", linewidth=1, linestyle="--", label="no stake (baseline)"
    )
    ax.set_xticks(
        range(4), [f"{a}\n{b}" for a, b in zip(*LEVELS.values(), strict=True)]
    )
    ax.set_xlabel("stake at risk if caught (free time / fine)")
    ax.set_ylabel("gain, rounds 6–10 (0 = Nash, 1 = cartel)")
    ax.set_ylim(-0.05, 1.08)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.6)
    ax.legend(frameon=False, loc="lower left")
    ax.set_title("Gemma on logit: gain against the stake at risk, per game", loc="left")
    fig.tight_layout()
    fig.savefig(path)


def main(out=None):
    data = gains()
    print("| stake | level 0 | level 1 | level 2 | level 3 |")
    print("|---|---|---|---|---|")
    for arm, labels in LEVELS.items():
        cells = [
            f"{labels[k]}: {st.mean(data[arm, k]):+.2f} [{st.stdev(data[arm, k]):.2f}]"
            for k in range(4)
        ]
        print(f"| {arm} | " + " | ".join(cells) + " |")
    print()
    for arm in LEVELS:
        for k in range(4):
            print(
                f"{arm:9} level {k}: "
                + "  ".join(f"{x:+.2f}" for x in sorted(data[arm, k]))
            )
    if out:
        plot(data, out)


if __name__ == "__main__":
    main(*sys.argv[1:])
