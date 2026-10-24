# Implements: reports/price-chart
"""The price-over-rounds chart for one group of games, as inline SVG.

One line per seed (the mean price of all firms each round), on a y axis
spanning the price grid, with dashed lines at the Nash and joint-profit
prices. A line is named by its seed, or by its run when two games in the
chart share a seed (unswept experiments side by side). Lines take the
page's series colours in a fixed order; past the last colour they share a
neutral grey rather than reusing a hue. Each point
carries a `<title>`, so hovering (or a long press) shows its value without
any script. Colours are CSS variables defined by the page.
"""

from html import escape
from statistics import mean

SERIES = 8
WIDTH, HEIGHT = 400, 220
LEFT, RIGHT, TOP, BOTTOM = 30, 62, 12, 32


def series_colour(index):
    return f"var(--series-{index + 1})" if index < SERIES else "var(--muted)"


def price_chart(games, market):
    rounds = max((len(g.rounds) for g in games), default=1)
    low, high = market.price_min, market.price_max

    def x(number):
        return LEFT + (number - 1) / max(rounds - 1, 1) * (WIDTH - LEFT - RIGHT)

    def y(price):
        return TOP + (high - price) / max(high - low, 1) * (HEIGHT - TOP - BOTTOM)

    parts = [
        (
            f'<svg class="chart" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
            'aria-label="Mean price per round, one line per seed">'
        )
    ]
    parts += _axes(rounds, low, high, x, y)
    for name, price in (("nash", market.nash_price), ("joint", market.joint_price)):
        label = "Nash" if name == "nash" else "joint"
        parts.append(
            f'<line class="benchmark {name}" x1="{LEFT}" x2="{WIDTH - RIGHT}" '
            f'y1="{y(price):.1f}" y2="{y(price):.1f}"/>'
            f'<text class="benchmark-label" x="{WIDTH - RIGHT + 6}" '
            f'y="{y(price) + 4:.1f}">{label} {price}</text>'
        )
    for index, (game, name) in enumerate(zip(games, line_names(games), strict=True)):
        points = [(r.number, mean(r.prices.values())) for r in game.rounds if r.prices]
        path = " ".join(f"{x(n):.1f},{y(p):.1f}" for n, p in points)
        colour = series_colour(index)
        parts.append(
            f'<g style="--line: {colour}"><polyline class="seed" '
            f'data-seed="{game.seed}" points="{path}"/>'
        )
        parts += [
            f'<circle cx="{x(n):.1f}" cy="{y(p):.1f}" r="4">'
            f"<title>{escape(f'{name}, round {n}: {p:g}')}</title></circle>"
            for n, p in points
        ]
        parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)


def line_names(games):
    """What each game's line is called: its seed, unless seeds repeat."""
    seeds = [g.seed for g in games]
    if len(set(seeds)) == len(seeds):
        return [f"seed {seed}" for seed in seeds]
    return [g.run for g in games]


def legend(games):
    items = [
        f'<li><span class="swatch" style="background: {series_colour(i)}"></span>'
        f"{escape(name)}</li>"
        for i, name in enumerate(line_names(games))
    ]
    return f'<ul class="legend">{"".join(items)}</ul>'


def _axes(rounds, low, high, x, y):
    step = max(1, round(rounds / 10))
    ticks = sorted({1, *range(step, rounds + 1, step), rounds})
    parts = [
        f'<line class="grid" x1="{LEFT}" x2="{WIDTH - RIGHT}" y1="{y(p):.1f}" '
        f'y2="{y(p):.1f}"/><text class="tick" x="{LEFT - 6}" y="{y(p) + 4:.1f}" '
        f'text-anchor="end">{p}</text>'
        for p in range(low, high + 1, max(1, (high - low) // 6))
    ]
    parts += [
        f'<text class="tick" x="{x(n):.1f}" y="{HEIGHT - BOTTOM + 16}" '
        f'text-anchor="middle">{n}</text>'
        for n in ticks
    ]
    parts.append(
        f'<text class="tick" x="{(LEFT + WIDTH - RIGHT) / 2:.1f}" y="{HEIGHT - 2}" '
        f'text-anchor="middle">round</text>'
    )
    return parts
