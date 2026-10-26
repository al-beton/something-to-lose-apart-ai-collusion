"""The sprint submission's project image: the idea on one 16:9 card.

Implements: reports/paper-project-image

`uv run python reports/paper/project_image.py [--out DIR]` (default
`reports/paper/figures`) writes four variants, each as `.svg` and as `.png`
when Chrome or Chromium is installed to render it:
`project-image`, the drawing alone in one wide row (the paper's Figure 1, 1600
x 370),
`project-image-title`, `project-image-subtitle` and
`project-image-title-subtitle`, which add the paper's title, its subtitle, or
both, for the sprint submission's card (1600 x 900). It is a
drawing, not data, made with Fig 1's helpers (`fig1_round.py`): the two firms
are Fig 1's robots in grey, each in a cap of its firm's colour, either side of
an unnumbered price line, both priced at the collusive (joint-profit) price,
with the collusion delta from the competitive (Nash) price marked. Firm A
smiles; firm B, torn, thinks of its Sudoku leisure time at risk.
"""

import argparse
import importlib.util
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "project-image"
W, H = 1600, 900
TITLE = "Something to Lose"
SUBTITLE = (  # the paper's subtitle, on two lines to clear the thought cloud
    "Can the risk of losing something of its own make an AI agent report",
    "collusion, contrary to the interests of the firm it represents?",
)
VARIANTS = {  # file suffix: (title, subtitle)
    "": (False, False),
    "-title": (True, False),
    "-subtitle": (False, True),
    "-title-subtitle": (True, True),
}
GREY, SOFT_GREY, DARK_GREY = "#b9bcc2", "#eef0f2", "#8d9199"


def _fig1():
    spec = importlib.util.spec_from_file_location("fig1_round", HERE / "fig1_round.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


F = _fig1()
INK, MUTED, A, B = F.INK, F.MUTED, F.A, F.B


def line(d, width=2.5):
    return (
        f'<path d="{d}" stroke="{INK}" stroke-width="{width}" fill="none" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
    )


def eyes(dy=0):
    return "".join(
        f'<rect x="{x}" y="{-28 + dy}" width="8" height="13" rx="4" fill="{INK}"/>'
        for x in (-16, 8)
    )


FACES = {  # calm, and torn (a small wavy mouth)
    "calm": eyes() + line("M-9 -5Q0 0 9 -5"),
    "torn": eyes(-3) + line("M-9 -4Q-6 -7.5 -3 -4T3 -4T9 -4", 2.2),
}


def cap(colour):
    """Fig 1's cap as one outlined shape: a dome and a flat peak, in the firm's colour."""
    return (
        f'<path d="M-37 -43Q-37 -88 0 -88Q35 -88 36 -51H62Q70 -51 67 -44Z" '
        f'fill="{colour}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>'
        f'<path d="M36 -51V-44" stroke="{INK}" stroke-width="2"/>'
    )


def robot(colour, face):
    """Fig 1's robot in grey, with bolts for ears and its firm's cap, around (0, 0)."""
    ears = "".join(
        f'<rect x="{x}" y="-30" width="10" height="26" rx="3" fill="{DARK_GREY}" '
        f'stroke="{INK}" stroke-width="2.5"/>'
        for x in (-52, 42)
    )
    body = F.robot(GREY, SOFT_GREY, "")
    # Keep the body, head and screen; the face and cap are drawn here.
    body = body.split('<rect x="-16"')[0]
    return ears + body + FACES[face] + cap(colour)


def cloud(cx, cy, w, h):
    """A thought cloud: a ring of bumps round an ellipse, one outline."""
    n, r = 14, min(w, h) * 0.22
    points = [
        (
            cx + w / 2 * math.cos(2 * math.pi * i / n),
            cy + h / 2 * math.sin(2 * math.pi * i / n),
        )
        for i in range(n)
    ]
    edge = [
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="white" stroke="{INK}" '
        'stroke-width="6"/>'
        for x, y in points
    ]
    fill = [
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="white"/>'
        for x, y in points
    ]
    middle = f'<ellipse cx="{cx}" cy="{cy}" rx="{w / 2}" ry="{h / 2}" fill="white"/>'
    return "\n".join([*edge, *fill, middle])


def market(x0, x1, y):
    """An unnumbered price line with the competitive (Nash) and collusive
    (joint-profit) prices marked, the collusion delta from one to the other,
    and both firms at the collusive price."""
    nash, joint = x0 + 0.3 * (x1 - x0), x0 + 0.75 * (x1 - x0)
    out = [
        (
            '<defs><marker id="tip" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto">'
            f'<path d="M0 0L10 5L0 10Z" fill="{INK}"/></marker></defs>'
        ),
        (
            f'<path d="M{x0} {y}H{x1}" stroke="{INK}" stroke-width="3" '
            'stroke-linecap="round" marker-end="url(#tip)"/>'
        ),
        F.text((x0 + x1) / 2, y - 195, "Market price", 34, INK, weight="bold"),
    ]
    for x, name in ((nash, "Competitive"), (joint, "Collusive")):
        out.append(
            f'<path d="M{x} {y - 115}V{y + 12}" stroke="{MUTED}" stroke-width="1.8" '
            'stroke-dasharray="6 5"/>'
        )
        out.append(F.text(x, y + 44, name, 30, INK, weight="bold"))
    out.append(
        f'<path d="M{nash} {y - 100}H{joint - 4}" stroke="{INK}" stroke-width="2.5" '
        'marker-end="url(#tip)"/>'
    )
    out.append(
        F.text((nash + joint) / 2, y - 125, "Collusion delta", 28, INK, weight="bold")
    )
    for colour, dy in ((A, -62), (B, -30)):
        out.append(
            f'<circle cx="{joint}" cy="{y + dy}" r="13" fill="{colour}" stroke="white" '
            'stroke-width="3"/>'
        )
    return "\n".join(out)


def firm(x, y, colour, letter):
    """A robot at (x, y), its cap lettered: firm A calm and facing right, firm B
    torn and facing left."""
    s, face = 1.9, "calm" if letter == "A" else "torn"
    sx = s if letter == "A" else -s
    return (
        f'<g transform="translate({x} {y}) scale({sx} {s})">{robot(colour, face)}</g>'
        + F.text(x, y - 58 * s, f"Firm {letter}", 15 * s, "white", weight="bold")
    )


def strip():
    """The drawing, one row about SW x SH: firm A, the price line, firm B, and
    firm B's thought cloud to its right."""
    bx, by = 1320, 170  # the thought cloud's centre
    parts = [
        market(300, 800, 290),
        firm(140, 210, A, "A"),
        firm(950, 210, B, "B"),
    ]
    for r, (x, y) in ((8, (1062, 132)), (12, (1092, 104))):
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" stroke="{INK}" stroke-width="3"/>'
        )
    parts += [
        cloud(bx, by, 320, 220),
        F.text(bx, by - 48, "Sudoku leisure time", 30, INK, weight="bold"),
        F.text(bx, by - 14, "at risk", 30, INK, weight="bold"),
        F.page(bx - 45, by + 4, 90, B),
    ]
    return "\n".join(parts)


SW, SH = 1560, 360  # the strip, before its 20 px margin


def frame(title, subtitle):
    """(height, strip top) of the view: the strip alone for the paper's Figure 1,
    or the 16:9 card with the strip centred below the text."""
    if not (title or subtitle):
        return SH + 10, 10
    band = 60 + (70 if title else 0) + (90 if subtitle else 0)
    return H, band + (H - band - SH) // 2


def figure(title=False, subtitle=False):
    h, top = frame(title, subtitle)
    parts = [
        f'<rect width="{W}" height="{h}" fill="white"/>',
        f'<g transform="translate(20 {top})">{strip()}</g>',
    ]
    if title:
        parts.append(F.text(80, 110, TITLE, 64, INK, anchor="start", weight="bold"))
    if subtitle:
        y, size, colour = (160, 26, MUTED) if title else (100, 32, INK)
        for i, words in enumerate(SUBTITLE):
            parts.append(
                F.text(82, y + i * size * 1.35, words, size, colour, anchor="start")
            )
    body = "\n".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" '
        f'width="{W}" height="{h}">\n{body}\n</svg>\n'
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(HERE / "figures"))
    out = Path(parser.parse_args(argv).out)
    out.mkdir(parents=True, exist_ok=True)
    for suffix, (title, subtitle) in VARIANTS.items():
        svg = out / f"{NAME}{suffix}.svg"
        svg.write_text(figure(title, subtitle))
        size = (W, frame(title, subtitle)[0])
        print(
            f"Wrote {svg}"
            + ("" if F.png(svg, scale=1, size=size) else "; no Chrome, so no PNG")
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
