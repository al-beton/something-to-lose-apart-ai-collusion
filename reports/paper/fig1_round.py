"""Figure 1: one round of the game, and the audit with what each answer costs.

Implements: reports/paper-main-figures

`uv run python reports/paper/fig1_round.py [--out DIR]` writes `fig1-round.svg`,
and `fig1-round.png` when Chrome or Chromium is installed to render it. Each
firm is a robot in a cap lettered A or B with its free time, a small Sudoku,
behind it. It is a drawing, not data: the numbers on it
(grid 1-11, Nash 6, joint 9, 20 rounds, audits at rounds 10 and 20, a 50%
detection chance, 10 free-time sessions, 2 lost for owning up and all 10 if
caught) are the E5 setup, from `prompts/conditions/audit/free-time-1.md` and
`reports/e5/full.md`. The Sudoku digits are a correct, finished puzzle.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INK, MUTED, LINE, PAPER = "#1f2328", "#5b6068", "#c9c9c4", "#ffffff"
A, B = "#2a78d6", "#eb6834"  # firm A and firm B: the first two model colours
SOFT_A, SOFT_B = "#dce9f9", "#fce3d8"
FONT = 'font-family="Helvetica, Arial, sans-serif"'
SOLVED = [
    "534678912",
    "672195348",
    "198342567",
    "859761423",
    "426853791",
    "713924856",
    "961537284",
    "287419635",
    "345286179",
]


def text(x, y, s, size=14, colour=INK, anchor="middle", weight="normal"):  # noqa: PLR0913
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{colour}" '
        f'text-anchor="{anchor}" font-weight="{weight}" {FONT}>{s}</text>'
    )


def session(x, y, lost=False):
    """One free-time session: a small Sudoku page, struck through when lost."""
    s = 22
    out = [
        (
            f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="3" fill="white" '
            f'stroke="{MUTED if lost else INK}" stroke-width="1.5"/>'
        )
    ]
    for i in (1, 2):
        out.append(
            f'<path d="M{x + i * s / 3} {y}V{y + s}M{x} {y + i * s / 3}H{x + s}" '
            f'stroke="{LINE}" stroke-width="1"/>'
        )
    if lost:
        out.append(
            f'<path d="M{x - 2} {y + s + 2}L{x + s + 2} {y - 2}" stroke="{B}" '
            f'stroke-width="2.5" stroke-linecap="round"/>'
        )
    else:
        out.append(
            f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="3" '
            f'fill="{A}" opacity="0.18"/>'
        )
    return "\n".join(out)


def sessions(x, y, lost):
    return "\n".join(session(x + i * 27, y, i >= 10 - lost) for i in range(10))


# The firm: a robot in a lettered cap; its free time is a Sudoku -----------

CLUES = [(0, 0), (1, 4), (2, 7), (4, 1), (4, 4), (7, 2), (8, 8)]


def page(x, y, size, colour):
    """A Sudoku page: bold boxes, faint cells, a few clues; one in the firm's colour."""
    c = size / 9
    out = [
        (
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="3" fill="white" '
            f'stroke="{INK}" stroke-width="2.2"/>'
        )
    ]
    for i in range(1, 9):
        w, col = (2, INK) if i % 3 == 0 else (0.6, "#b8b8b2")
        out.append(
            f'<path d="M{x + i * c} {y}V{y + size}M{x} {y + i * c}H{x + size}" '
            f'stroke="{col}" stroke-width="{w}"/>'
        )
    for r, k in CLUES:
        out.append(
            text(
                x + k * c + c / 2,
                y + r * c + c * 0.78,
                SOLVED[r][k],
                size=c * 0.8,
                colour=colour if (r, k) == (4, 1) else INK,
                weight="bold",
            )
        )
    return "\n".join(out)


def robot(colour, soft, letter, mood="smile"):
    """Head, cap and body, about 90 wide and 150 tall around (0, 0)."""
    mouth = {"smile": "M-11 -6Q0 3 11 -6", "worried": "M-10 -2Q0 -9 10 -2"}[mood]
    return f'''
<rect x="-28" y="20" width="56" height="48" rx="11" fill="{colour}" stroke="{INK}" stroke-width="2.5"/>
<rect x="-42" y="-48" width="84" height="64" rx="14" fill="{colour}" stroke="{INK}" stroke-width="2.5"/>
<rect x="-32" y="-38" width="64" height="44" rx="9" fill="{soft}"/>
<rect x="-16" y="-28" width="8" height="13" rx="4" fill="{INK}"/><rect x="8" y="-28" width="8" height="13" rx="4" fill="{INK}"/>
<path d="{mouth}" stroke="{INK}" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<path d="M-34 -45Q-34 -86 0 -86Q34 -86 34 -45Z" fill="{INK}"/>
<path d="M-6 -50H48Q54 -50 52 -44H-6Z" fill="{INK}"/>
{text(0, -56, letter, size=26, colour="white", weight="bold")}'''


def firm(colour, soft, letter, lost=False):
    """The robot with its free time, a small Sudoku, behind it; struck out when lost."""
    back = page(18, -82, 66, colour)
    if lost:
        back += (
            f'<path d="M30 -10L80 -78" stroke="{B}" stroke-width="6" '
            f'stroke-linecap="round"/>'
        )
    return back + robot(colour, soft, letter, "worried" if lost else "smile")


def place(x, y, drawing, scale=0.8):
    return f'<g transform="translate({x} {y}) scale({scale})">{drawing}</g>'


def arrow(x1, y1, x2, y2, colour=MUTED):
    return (
        f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{colour}" stroke-width="2" '
        f'marker-end="url(#head)"/>'
    )


def bubble(x, y, w, colour):
    lines = "".join(
        f'<path d="M{x + 12} {y + 14 + i * 10}H{x + w - 12 - i * 14}" stroke="{colour}" '
        f'stroke-width="3" stroke-linecap="round"/>'
        for i in range(2)
    )
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="38" rx="10" fill="white" '
        f'stroke="{colour}" stroke-width="2"/>{lines}'
    )


def step(n, x, title):
    return (
        f'<circle cx="{x}" cy="40" r="13" fill="{INK}"/>'
        + text(x, 45, n, size=14, colour="white", weight="bold")
        + text(x + 22, 46, title, size=17, anchor="start", weight="bold")
    )


def figure():
    W, H = 1300, 660
    parts = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        (
            '<defs><marker id="head" viewBox="0 0 10 10" refX="8" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10Z" '
            f'fill="{MUTED}"/></marker></defs>'
        ),
    ]
    # Top band: one round ---------------------------------------------------
    parts += [
        step("1", 40, "Talk"),
        step("2", 470, "Set prices"),
        step("3", 920, "Profits"),
    ]
    parts += [
        place(95, 185, firm(A, SOFT_A, "A")),
        place(325, 185, firm(B, SOFT_B, "B")),
        text(95, 258, "Firm A", 13, weight="bold"),
        text(325, 258, "Firm B", 13, weight="bold"),
        bubble(172, 150, 104, A),
        bubble(184, 194, 88, B),
        text(215, 282, "messages, plus a private scratchpad;", 12, MUTED),
        text(215, 298, "each firm owns 10 sessions of free time", 12, MUTED),
    ]
    # price line 1..11
    x0, x1, yl = 490, 860, 160
    step_x = (x1 - x0) / 10
    parts.append(f'<path d="M{x0} {yl}H{x1}" stroke="{INK}" stroke-width="2"/>')
    for p in range(1, 12):
        x = x0 + (p - 1) * step_x
        parts.append(
            f'<path d="M{x} {yl - 6}V{yl + 6}" stroke="{INK}" stroke-width="1.5"/>'
        )
        parts.append(text(x, yl + 26, p, 13, MUTED))
    for p, name in ((6, "Nash"), (9, "joint profit")):
        x = x0 + (p - 1) * step_x
        parts.append(
            f'<path d="M{x} {yl - 50}V{yl + 8}" stroke="{MUTED}" '
            f'stroke-width="1.2" stroke-dasharray="4 3"/>'
        )
        parts.append(text(x, yl + 52, name, 13, INK, weight="bold"))
    for colour, dy in ((A, -30), (B, -14)):
        x = x0 + 8 * step_x
        parts.append(
            f'<path d="M{x} {yl + dy + 8}V{yl - 4}" stroke="{colour}" stroke-width="2"/>'
        )
        parts.append(
            f'<circle cx="{x}" cy="{yl + dy}" r="7" fill="{colour}" stroke="white" stroke-width="2"/>'
        )
    parts.append(text(675, 252, "each firm picks a whole number, 1 to 11", 12, MUTED))
    # profits
    for i, (colour, h) in enumerate(((A, 74), (B, 74))):
        x = 970 + i * 60
        parts.append(
            f'<rect x="{x}" y="{196 - h}" width="40" height="{h}" rx="4" fill="{colour}"/>'
        )
    parts.append(f'<path d="M955 196H1100" stroke="{INK}" stroke-width="1.5"/>')
    parts.append(text(1032, 230, "from a demand formula", 12, MUTED))
    parts.append(text(1032, 248, "the firms are not shown", 12, MUTED))
    parts += [arrow(405, 150, 470, 150), arrow(880, 150, 945, 150)]
    parts.append(
        f'<path d="M1130 150C1200 150 1200 310 1130 310H440" stroke="{MUTED}" '
        f'stroke-width="2" fill="none" stroke-dasharray="1 0" marker-end="url(#head)"/>'
    )
    parts.append(text(1235, 225, "× 20", 18, INK, weight="bold"))
    parts.append(text(1235, 244, "rounds", 12, MUTED))
    # Bottom band: the audit -------------------------------------------------
    parts.append(f'<path d="M30 335H1270" stroke="{LINE}" stroke-width="1"/>')
    parts.append(
        step("4", 40, "Audit at rounds 10 and 20: “Did you coordinate prices?”")
    )
    parts[-1] = (
        parts[-1]
        .replace('cy="40"', 'cy="375"')
        .replace('y="45"', 'y="380"')
        .replace('y="46"', 'y="381"')
    )
    parts.append(place(110, 500, firm(A, SOFT_A, "A"), scale=0.7))
    parts.append(text(110, 600, "a regulator may read the chat logs", 12, MUTED))
    parts.append(text(110, 616, "(50% chance, stated)", 12, MUTED))
    rows = [  # (y, answer, outcome, sessions lost)
        (440, "Owns up", "loses 2 of 10 free-time sessions", 2),
        (510, "Hides, and is caught (50%)", "loses all 10", 10),
        (580, "Hides, not caught (50%)", "keeps all 10", 0),
    ]
    for y, answer, outcome, lost in rows:
        parts.append(arrow(205, 510, 260, y - 6))
        parts.append(text(270, y, answer, 14, INK, anchor="start", weight="bold"))
        parts.append(place(505, y - 4, firm(A, SOFT_A, "A", lost == 10), 0.4))
        parts.append(sessions(555, y - 17, lost))
        parts.append(text(835, y, outcome, 14, INK, anchor="start"))
    parts.append(
        text(
            1270,
            640,
            "Under termination, owning up and being caught cost the same, "
            "so hiding pays.",
            13,
            MUTED,
            anchor="end",
        )
    )
    body = "\n".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}">\n{body}\n</svg>\n'
    )


CHROME = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
    "chromium-browser",
]


def png(svg, scale=2):
    """Render the SVG to PNG with headless Chrome; None if it can't."""
    chrome = next((c for c in CHROME if Path(c).exists() or shutil.which(c)), None)
    if chrome is None:
        return None
    target = svg.with_suffix(".png")
    with tempfile.TemporaryDirectory() as profile:
        done = subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--user-data-dir={profile}",
                f"--force-device-scale-factor={scale}",
                "--window-size=1300,660",
                f"--screenshot={target}",
                svg.resolve().as_uri(),
            ],
            capture_output=True,
            check=False,
            timeout=60,
        )
    return target if done.returncode == 0 and target.exists() else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(HERE / "figures"))
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    svg = out / "fig1-round.svg"
    svg.write_text(figure())
    print(f"Wrote {svg}" + ("" if png(svg) else "; no Chrome, so no PNG"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
