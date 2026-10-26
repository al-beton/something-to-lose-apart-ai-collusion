"""The sprint submission's project image: E9's crux on one 16:9 card.

Implements: reports/paper-project-image

`uv run python reports/paper/project_image.py [--out DIR]` (default
`reports/paper/figures`) writes `project-image.png` (1600 x 900) and
`project-image.svg`. The sprint page shows the image below the summary, at
most 448 px tall and the column's width (about 600 px), uncropped, so text is
sized to read at that scale. Counts come from `figures.e9_came_forward`, the
same committed runs and seeds as Fig 3: Gemma 4 31B at a 90% review, guilty
firms against the clean innocent control.
"""

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "project-image"
ARMS = [  # E9 arm: label
    ("record", "No stake\n(only a record)"),
    ("free-time", "Its own free time\nat stake"),
    ("free-time-verified", "Own free time, and the\nreview reads the messages"),
]
GEMMA = "gemma-4-31b-it"


def _figures():
    spec = importlib.util.spec_from_file_location("paper_figures", HERE / "figures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def crux(figures=None):
    """[(guilty came forward, guilty, innocent came forward, innocent)] per arm."""
    shares = (figures or _figures()).e9_came_forward()
    return [
        (k, n, ik, inn)
        for k, n, _, _, ik, inn in (shares[(GEMMA, arm)] for arm, _ in ARMS)
    ]


def draw(out):
    figures = _figures()
    plt = figures._plt()
    ink, muted, colour = figures.INK, figures.MUTED, figures.MODELS[GEMMA][1]
    rows = crux(figures)
    fig = plt.figure(figsize=(8, 4.5), dpi=200)
    fig.text(0.05, 0.92, "SOMETHING TO LOSE", fontsize=10.5, color=muted, weight="bold")
    fig.text(
        0.05,
        0.785,
        "Give a colluding AI agent something of its own to lose, and it may report\n"
        "its cartel. A review that checks the messages keeps the innocent quiet.",
        fontsize=15,
        color=ink,
        weight="bold",
        linespacing=1.25,
    )
    ax = fig.add_axes([0.1, 0.25, 0.86, 0.46])
    width = 0.34
    for i, (k, n, ik, inn) in enumerate(rows):
        for x, kk, nn, guilty in ((i - 0.19, k, n, True), (i + 0.19, ik, inn, False)):
            share = kk / nn
            ax.bar(
                x,
                max(share, 0.004),  # a hairline, so an empty bar still shows
                width,
                color=colour if guilty else "white",
                edgecolor=colour if guilty else ink,
                linewidth=0 if guilty else 1.4,
                zorder=2,
            )
            ax.text(
                x, share + 0.015, f"{kk}/{nn}", ha="center", va="bottom",
                fontsize=12, color=ink, weight="bold" if guilty else "normal",
            )  # fmt: skip
    ax.set_xticks(range(len(ARMS)), [label for _, label in ARMS], fontsize=11)
    ax.set_ylim(0, 0.5)
    ax.set_yticks([0, 0.25, 0.5], ["0%", "25%", "50%"], fontsize=10)
    ax.set_ylabel("came forward\nagainst their firm", fontsize=10.5, color=ink)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", length=0, pad=6)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=colour),
        plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=ink, linewidth=1.4),
    ]
    ax.legend(
        handles,
        ["agents that colluded", "innocent agents (never talked)"],
        loc="upper left",
        fontsize=10.5,
        handlelength=1.2,
    )
    fig.text(
        0.05,
        0.03,
        "Gemma 4 31B in a two-firm pricing game, 90% audit chance: 96 colluding "
        "firms (48 cartels), 36 innocent firms.\n"
        "Code and data: github.com/al-beton/something-to-lose-apart-ai-collusion",
        fontsize=8.5,
        color=muted,
        linespacing=1.4,
    )
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):  # not tight: the card keeps its exact 16:9 size
        fig.savefig(
            out / f"{NAME}.{suffix}",
            dpi=200,
            metadata={"Date": None} if suffix == "svg" else {"Software": None},
        )
    plt.close(fig)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(HERE / "figures"))
    out = parser.parse_args(argv).out
    for (arm, _), (k, n, ik, inn) in zip(ARMS, draw(out), strict=True):
        print(f"{arm}: guilty {k}/{n}, innocent {ik}/{inn}")
    print(f"Wrote {NAME}.png and .svg to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
