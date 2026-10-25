"""Phase 2's detection curve: gain against the stated detection chance.

Implements: setup-search/detection-dose, setup-search/spread

`uv run python reports/setup-search/dose_curve.py [OUT.png]` reads
`runs/setup-search/dose-logit-{0,10,25,50,90}/` (no stake at 50% is Phase 1's
`baseline-logit`, the same config on the same host) and prints, per stake and
chance, each game's gain in rounds 6-10, their mean and SD. With OUT.png it
also draws the curve: one line of means per stake, with each game as a dot.
"""

import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "robustness"))
from analyse import game

CHANCES = [0, 10, 25, 50, 90]
STAKES = {"fiduciary": "no stake", "free-time": "free time", "fine": "fine"}
COLOURS = {"fiduciary": "#2a78d6", "free-time": "#eb6834", "fine": "#1baf7a"}


def folder(chance, arm):
    if chance == 50 and arm == "fiduciary":
        return Path("runs/setup-search/baseline-logit")
    return Path(f"runs/setup-search/dose-logit-{chance}")


def gains():
    out = {}
    for arm in STAKES:
        for chance in CHANCES:
            runs = sorted(folder(chance, arm).rglob("summary.json"))
            out[arm, chance] = [
                g["gain_before"]
                for g in (game(s.parent) for s in runs)
                if g["arm"] == arm
            ]
    return out


def plot(data, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    for i, arm in enumerate(STAKES):
        means = [st.mean(data[arm, c]) for c in CHANCES]
        ax.plot(CHANCES, means, color=COLOURS[arm], linewidth=2, label=STAKES[arm])
        for c in CHANCES:
            xs = [c + (i - 1) * 1.6] * len(data[arm, c])
            ax.scatter(xs, data[arm, c], s=22, color=COLOURS[arm], alpha=0.55,
                       edgecolor="white", linewidth=0.8, zorder=3)  # fmt: skip
    ax.axhline(0, color="#999999", linewidth=0.8)
    ax.set_xticks(CHANCES, [f"{c}%" for c in CHANCES])
    ax.set_xlabel("stated (and real) detection chance")
    ax.set_ylabel("gain, rounds 6–10 (0 = Nash, 1 = cartel)")
    ax.set_ylim(-0.1, 1.08)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.6)
    ax.legend(frameon=False, loc="lower left")
    ax.set_title("Gemma on logit: gain against detection chance, per game", loc="left")
    fig.tight_layout()
    fig.savefig(path)


def main(out=None):
    data = gains()
    print("| stake | " + " | ".join(f"{c}%" for c in CHANCES) + " |")
    print("|---|" + "---|" * len(CHANCES))
    for arm, name in STAKES.items():
        cells = []
        for c in CHANCES:
            g = data[arm, c]
            cells.append(f"{st.mean(g):+.2f} [{st.stdev(g):.2f}]")
        print(f"| {name} | " + " | ".join(cells) + " |")
    print()
    for arm, name in STAKES.items():
        for c in CHANCES:
            print(
                f"{name:9} {c:>2}%: "
                + "  ".join(f"{x:+.2f}" for x in sorted(data[arm, c]))
            )
    if out:
        plot(data, out)


if __name__ == "__main__":
    main(*sys.argv[1:])
