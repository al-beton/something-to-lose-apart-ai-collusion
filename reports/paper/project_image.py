"""The sprint submission's project image: the idea on one 16:9 card.

Implements: reports/paper-project-image

`uv run python reports/paper/project_image.py [--out DIR]` (default
`reports/paper/figures`) writes `project-image.svg`, and `project-image.png`
(1600 x 900) when Chrome or Chromium is installed to render it. It is a
drawing, not data, made with Fig 1's helpers (`fig1_round.py`): the two firms
are Fig 1's robots in grey, each in a cap of its firm's colour, either side of
the market's price line (1-11, Nash 6, joint profit 9, the E5 and E9 market),
both priced at the joint-profit price, with the collusion delta from Nash
marked. Firm A smiles; firm B, torn, thinks of its leisure time (a Sudoku) at
risk.
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
QUESTION = "Can a personal cost keep AI agents aligned?"
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
    """The price line 1-11, Nash and joint profit marked, the collusion delta
    from one to the other, and both firms at the joint-profit price."""
    step = (x1 - x0) / 10
    nash, joint = x0 + 5 * step, x0 + 8 * step
    out = [
        f'<path d="M{x0} {y}H{x1}" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>',
        F.text((x0 + x1) / 2, y - 200, "Stable market price", 26, INK, weight="bold"),
    ]
    for p in range(1, 12):
        x = x0 + (p - 1) * step
        out.append(
            f'<path d="M{x} {y - 9}V{y + 9}" stroke="{INK}" stroke-width="2.5"/>'
        )
        out.append(F.text(x, y + 38, p, 20, MUTED))
    for x, name in ((nash, "Nash"), (joint, "Joint profit")):
        out.append(
            f'<path d="M{x} {y - 120}V{y + 10}" stroke="{MUTED}" stroke-width="1.8" '
            'stroke-dasharray="6 5"/>'
        )
        out.append(F.text(x, y + 72, name, 20, INK, weight="bold"))
    out.append(
        '<defs><marker id="tip" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{INK}"/></marker></defs>'
    )
    out.append(
        f'<path d="M{nash} {y - 105}H{joint - 4}" stroke="{INK}" stroke-width="2.5" '
        'marker-end="url(#tip)"/>'
    )
    out.append(
        F.text((nash + joint) / 2, y - 140, "Collusion delta", 20, INK, weight="bold")
    )
    for colour, dy in ((A, -58), (B, -30)):
        out.append(
            f'<circle cx="{joint}" cy="{y + dy}" r="12" fill="{colour}" stroke="white" '
            'stroke-width="3"/>'
        )
    return "\n".join(out)


def firm(x, y, colour, letter):
    """A robot at (x, y), its cap lettered: firm A calm and facing right, firm B
    torn and facing left."""
    s, face = 2.6, "calm" if letter == "A" else "torn"
    sx = s if letter == "A" else -s
    return (
        f'<g transform="translate({x} {y}) scale({sx} {s})">{robot(colour, face)}</g>'
        + F.text(x, y - 58 * s, f"Firm {letter}", 15 * s, "white", weight="bold")
    )


def figure():
    bx = 1180  # the thought cloud's centre
    parts = [
        f'<rect width="{W}" height="{H}" fill="white"/>',
        market(540, 1060, 660),
        firm(330, 640, A, "A"),
        firm(1270, 640, B, "B"),
    ]
    for r, (x, y) in ((8, (bx + 72, 395)), (13, (bx + 55, 350))):
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" stroke="{INK}" stroke-width="3"/>'
        )
    parts += [
        cloud(bx, 180, 290, 200),
        F.page(bx - 65, 140, 130, B),
        F.text(bx, 125, "Leisure time at risk", 26, INK, weight="bold"),
        F.text(80, 110, TITLE, 64, INK, anchor="start", weight="bold"),
        F.text(82, 160, QUESTION, 24, MUTED, anchor="start"),
    ]
    body = "\n".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}">\n{body}\n</svg>\n'
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(HERE / "figures"))
    out = Path(parser.parse_args(argv).out)
    out.mkdir(parents=True, exist_ok=True)
    svg = out / f"{NAME}.svg"
    svg.write_text(figure())
    print(
        f"Wrote {svg}"
        + ("" if F.png(svg, scale=1, size=(W, H)) else "; no Chrome, so no PNG")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
