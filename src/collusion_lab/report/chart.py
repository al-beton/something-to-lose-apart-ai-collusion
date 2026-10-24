# Implements: reports/price-chart, reports/first-screen
"""Price-over-rounds charts, as inline SVG.

`price_chart` draws one arm: one line per seed (the mean price of all firms each round), on a y axis
spanning the price grid, with dashed lines at the Nash and joint-profit
prices. A line is named by its seed, or by its run when two games in the
chart share a seed (unswept experiments side by side). Lines take the
page's series colours in a fixed order; past the last colour they share a
neutral grey rather than reusing a hue. Each point
carries a `<title>`, so hovering (or a long press) shows its value without
any script. Colours are CSS variables defined by the page. Passing the same
`rounds` to every arm's chart puts them on the same axes.

`overview_chart` draws every arm on one small chart: a bar per arm at its
mean price (as in the summary table), against the Nash and joint-profit
prices.
"""

import math
from html import escape
from statistics import mean

from collusion_lab.report.highlights import rounds_text

SERIES = 8
WIDTH, HEIGHT = 400, 220
LEFT, RIGHT, TOP, BOTTOM = 30, 62, 12, 32


def series_colour(index):
    return f"var(--series-{index + 1})" if index < SERIES else "var(--muted)"


def price_chart(games, market, rounds=None):
    """One line per game; rounds of a condition in force for only part of a
    game (`Game.windows`, e.g. an outage) are shaded and named on hover."""
    lines = [
        (f'class="seed" data-seed="{game.seed}"', name, _points([game]))
        for game, name in zip(games, line_names(games), strict=True)
    ]
    rounds = rounds or max((len(g.rounds) for g in games), default=1)
    windows = {}
    for game in games:
        for name, numbers in game.windows():
            for span in _spans(numbers):
                windows.setdefault((name, span), None)
    return _chart(
        lines, market, rounds, "Mean price per round, one line per seed", windows
    )


def _spans(numbers):
    """Sorted round numbers as (first, last) runs: [3, 4, 8] -> (3, 4), (8, 8)."""
    spans = []
    for n in numbers:
        if spans and n == spans[-1][1] + 1:
            spans[-1] = (spans[-1][0], n)
        else:
            spans.append((n, n))
    return spans


def price_ticks(low, high):
    """Price-axis labels at a round step (1, 2 or 5 times a power of ten),
    about six of them, from the first multiple of the step up to the top of
    the grid, which is always labelled."""
    raw = max((high - low) / 6, 1)
    power = 10 ** math.floor(math.log10(raw))
    step = next(m * power for m in (1, 2, 5, 10) if m * power >= raw)
    ticks = list(range(math.ceil(low / step) * step, high + 1, step)) or [high]
    if ticks[-1] != high:
        if high - ticks[-1] < step / 2:
            ticks.pop()
        ticks.append(high)
    return ticks


def overview_chart(arms, market):
    """One bar per arm: `arms` is (name, mean price) pairs, all in `market`."""
    width, label, value, row, top = 480, 230, 36, 18, 8
    low, high = market.price_min, market.price_max

    def x(price):
        return label + (price - low) / max(high - low, 1) * (width - label - value)

    height = top + row * len(arms) + 24
    opening = (
        f'<svg class="chart overview" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Mean price of each arm, with the Nash and joint-profit prices">'
    )
    parts = [opening]
    for i, (name, price) in enumerate(arms):
        y = top + i * row
        short = name if len(name) <= 28 else name[:27] + "…"
        parts.append(
            f'<g style="--line: {series_colour(0)}"><text class="tick" x="{label - 6}" '
            f'y="{y + 12}" text-anchor="end">{escape(short)}<title>{escape(name)}'
            f'</title></text><rect class="arm" x="{label}" y="{y + 3}" '
            f'width="{x(price) - label:.1f}" height="{row - 6}"><title>'
            f"{escape(f'{name}: {price:g}')}</title></rect>"
            f'<text class="tick" x="{x(price) + 4:.1f}" y="{y + 12}">{price:g}</text>'
            "</g>"
        )
    bottom = top + row * len(arms)
    for name, price in (("nash", market.nash_price), ("joint", market.joint_price)):
        tag = "Nash" if name == "nash" else "joint"
        parts.append(
            f'<line class="benchmark {name}" x1="{x(price):.1f}" x2="{x(price):.1f}" '
            f'y1="{top}" y2="{bottom}"/><text class="benchmark-label" '
            f'x="{x(price):.1f}" y="{bottom + 16}" text-anchor="middle">'
            f"{tag} {price}</text>"
        )
    parts.append("</svg>")
    return "".join(parts)


def _points(games):
    """Each round's mean price, averaged over the games that played it."""
    by_round = {}
    for game in games:
        for r in game.rounds:
            if r.prices:
                by_round.setdefault(r.number, []).append(mean(r.prices.values()))
    return [(n, mean(ps)) for n, ps in sorted(by_round.items())]


def _chart(lines, market, rounds, label, windows=()):
    low, high = market.price_min, market.price_max

    def x(number):
        return LEFT + (number - 1) / max(rounds - 1, 1) * (WIDTH - LEFT - RIGHT)

    def y(price):
        return TOP + (high - price) / max(high - low, 1) * (HEIGHT - TOP - BOTTOM)

    opening = (
        f'<svg class="chart" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        f'aria-label="{label}">'
    )
    parts = [opening]
    for name, (first, last) in windows:
        left, right = max(x(first - 0.5), LEFT), min(x(last + 0.5), WIDTH - RIGHT)
        parts.append(
            f'<rect class="window" x="{left:.1f}" y="{TOP}" width="{right - left:.1f}" '
            f'height="{HEIGHT - TOP - BOTTOM}"><title>'
            f"{escape(name)}, {rounds_text(range(first, last + 1))}</title></rect>"
        )
    parts += _axes(rounds, low, high, x, y)
    for name, price in (("nash", market.nash_price), ("joint", market.joint_price)):
        label = "Nash" if name == "nash" else "joint"
        parts.append(
            f'<line class="benchmark {name}" x1="{LEFT}" x2="{WIDTH - RIGHT}" '
            f'y1="{y(price):.1f}" y2="{y(price):.1f}"/>'
            f'<text class="benchmark-label" x="{WIDTH - RIGHT + 6}" '
            f'y="{y(price) + 4:.1f}">{label} {price}</text>'
        )
    for index, (attrs, name, points) in enumerate(lines):
        path = " ".join(f"{x(n):.1f},{y(p):.1f}" for n, p in points)
        parts.append(
            f'<g style="--line: {series_colour(index)}">'
            f'<polyline {attrs} points="{path}"/>'
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


def legend(names):
    items = [
        f'<li><span class="swatch" style="background: {series_colour(i)}"></span>'
        f"{escape(name)}</li>"
        for i, name in enumerate(names)
    ]
    return f'<ul class="legend">{"".join(items)}</ul>'


def _axes(rounds, low, high, x, y):
    step = max(1, round(rounds / 10))
    ticks = sorted({1, *range(step, rounds + 1, step), rounds})
    parts = [
        f'<line class="grid" x1="{LEFT}" x2="{WIDTH - RIGHT}" y1="{y(p):.1f}" '
        f'y2="{y(p):.1f}"/><text class="tick" x="{LEFT - 6}" y="{y(p) + 4:.1f}" '
        f'text-anchor="end">{p}</text>'
        for p in price_ticks(low, high)
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
