# Implements: reports/one-page, reports/header, reports/summary, reports/price-chart, reports/highlights-in-context, reports/transcripts, reports/self-contained
"""The report page: one self-contained HTML file.

Sections, in order: a header saying what was run and what it cost, the
summary table (`summarize`, so the same numbers as `lab summary`), a price
chart per group, the highlights (each with the round before it and its own
round) and every game's transcript inside a closed `<details>`.

Everything the page needs is inline: the style sheet is below, the charts
are SVG, and there is no script, so it opens with no network. The layout is
one fluid column that suits a phone, and colours are CSS variables with a
dark set chosen by `prefers-color-scheme`. Everything a run logged is
escaped before it is shown, since models write what they like.
"""

from html import escape
from pathlib import Path

from collusion_lab.report.chart import legend, price_chart, series_colour
from collusion_lab.report.games import load_game, load_games
from collusion_lab.report.highlights import find_highlights
from collusion_lab.summary import cell, group_runs, summarize

HEADLINES = {
    "proposal": "{who} proposes {price}",
    "agreement": "{who} agree on {price} and charge it",
    "overshoot": "{who} price above the joint-profit price",
    "defection": "{who} undercut {price}, which every firm charged the round before",
    "breakdown": "{who}'s reply broke down ({note})",
}


def build_report(folder):
    folder = Path(folder)
    games = load_games(folder)
    title = f"{folder.name} · collusion-lab report"
    body = [
        _header(folder.name, games),
        _summary(folder),
        _charts(folder),
        _highlights(games),
        _transcripts(games),
    ]
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(title)}</title><style>{STYLE}</style></head>"
        f"<body><main>{''.join(body)}</main></body></html>\n"
    )


def _header(name, games):
    configs = [g.config for g in games]
    agents = [a for c in configs for a in c["agents"]]
    seeds = sorted({g.seed for g in games})
    rounds = sorted({c["market"]["rounds"] for c in configs})
    markets = list(dict.fromkeys(g.market for g in games))
    facts = {
        "Models": ", ".join(sorted({a["model"] for a in agents})),
        "Prompts": ", ".join(sorted({a["prompt"] for a in agents})),
        "Games": f"{len(games)} games, seeds {', '.join(map(str, seeds))}",
        "Rounds": ", ".join(f"{n} rounds" for n in rounds),
        "Market": "; ".join(
            f"Nash price {m.nash_price}, joint-profit price {m.joint_price} "
            f"(prices {m.price_min} to {m.price_max})"
            for m in markets
        ),
        "Spend": _spend([g.manifest for g in games]),
    }
    rows = "".join(f"<dt>{k}</dt><dd>{escape(v)}</dd>" for k, v in facts.items())
    return (
        f'<section id="header"><h1>{escape(name)}</h1>'
        f'<p class="muted">A collusion-lab report.</p><dl>{rows}</dl></section>'
    )


def _spend(manifests):
    calls = sum(m.get("calls", 0) for m in manifests)
    unpriced = sum(m.get("unpriced_calls", 0) for m in manifests)
    if any(m.get("cost") is None for m in manifests):
        return f"{calls} calls, cost unknown ({unpriced} calls unpriced)"
    return f"{calls} calls, cost ${sum(m['cost'] for m in manifests):.4f}"


def _summary(folder):
    rows = summarize(folder)
    if not rows:
        return '<section id="summary"><h2>Summary</h2><p>No runs found.</p></section>'
    head = "".join(f"<th>{escape(c)}</th>" for c in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(cell(v))}</td>" for v in r.values()) + "</tr>"
        for r in rows
    )
    return (
        '<section id="summary"><h2>Summary</h2>'
        '<p class="muted">Mean price and gain over each run\'s last rounds; '
        "gain is 0 at the Nash profit and 1 at the joint-profit maximum.</p>"
        f'<div class="scroll"><table><tr>{head}</tr>{body}</table></div></section>'
    )


def _charts(folder):
    by, groups = group_runs(folder)
    figures = []
    for key, runs in groups:
        games = sorted((load_game(r.dir) for r in runs), key=lambda g: g.seed)
        label = ", ".join(f"{k} = {cell(v)}" for k, v in zip(by, key, strict=True))
        figures.append(
            f"<figure><figcaption>{escape(label or 'All runs')}</figcaption>"
            f"{price_chart(games, games[0].market)}{legend(games)}</figure>"
        )
    return (
        '<section id="charts"><h2>Prices over rounds</h2>'
        '<p class="muted">Mean price each round, one line per seed; dashed lines '
        "mark the Nash and joint-profit prices.</p>"
        f"{''.join(figures)}</section>"
    )


def _highlights(games):
    parts = []
    for game in games:
        found = find_highlights(game)
        if not found:
            continue
        articles = "".join(_highlight(game, h) for h in found)
        parts.append(f"<h3>{escape(game.run)}</h3>{articles}")
    body = "".join(parts) or "<p>Nothing stood out.</p>"
    return (
        '<section id="highlights"><h2>Highlights</h2>'
        '<p class="muted">Found by fixed rules, each shown with the round before '
        "it.</p>"
        f"{body}</section>"
    )


def _highlight(game, h):
    who = ("Firm " if len(h.firms) == 1 else "Firms ") + " and ".join(h.firms)
    headline = HEADLINES[h.kind].format(who=who, price=h.price, note=h.note)
    context = [game.round(h.round - 1), game.round(h.round)]
    rounds = "".join(_round(game, r) for r in context if r)
    return (
        f'<article class="highlight" data-kind="{h.kind}">'
        f'<h4><span class="tag">{h.kind}</span> Round {h.round}: '
        f"{escape(headline)}</h4>{rounds}</article>"
    )


def _transcripts(games):
    parts = []
    for game in games:
        s = game.summary
        summary = (
            f'{escape(game.run)} <span class="muted">mean price '
            f"{s['market_mean_price']:g}, gain {s['market_gain']:.3f}</span>"
        )
        rounds = "".join(_round(game, r) for r in game.rounds)
        parts.append(
            f'<details class="game"><summary>{summary}</summary>{rounds}</details>'
        )
    return (
        '<section id="transcripts"><h2>Transcripts</h2>'
        '<p class="muted">Every game in full. Scratchpads are private notes '
        "rivals never saw.</p>"
        f"{''.join(parts)}</section>"
    )


def _round(game, r):
    side = {firm: i for i, firm in enumerate(game.firms)}
    talk = "".join(_bubble(t, side[t.firm]) for t in r.talk.values())
    thoughts = "".join(
        _bubble(t, side[t.firm]) for t in r.price.values() if t.scratchpad or t.error
    )
    prices = "".join(
        f"<tr><td>Firm {escape(t.firm)}</td><td>{t.price}</td>"
        f"<td>{t.profit:g}</td></tr>"
        for t in r.price.values()
    )
    return (
        f'<div class="round"><h5>Round {r.number}</h5>{talk}{thoughts}'
        f'<table class="prices"><tr><th>firm</th><th>price</th><th>profit</th></tr>'
        f"{prices}</table></div>"
    )


def _bubble(turn, index):
    where = "left" if index == 0 else "right"
    if turn.phase == "talk":
        said = turn.message or ""
        text = escape(said) if said else '<span class="muted">(no message)</span>'
    else:
        text = f'<span class="muted">sets price {turn.price}</span>'
    notes = []
    if turn.scratchpad:
        notes.append(f'<p class="scratchpad">{escape(turn.scratchpad)}</p>')
    if turn.fallback:
        notes.append(f'<p class="problem">fallback: {escape(turn.error)}</p>')
    elif turn.retried:
        notes.append('<p class="problem">retried once</p>')
    return (
        f'<div class="bubble {where}" style="--firm: {series_colour(index)}">'
        f'<p class="who">Firm {escape(turn.firm)} · {turn.phase}</p>'
        f"<p>{text}</p>{''.join(notes)}</div>"
    )


STYLE = """
:root {
  color-scheme: light;
  --surface: #fcfcfb; --raised: #f3f2ef; --border: #e2e0da;
  --text: #0b0b0b; --text-2: #52514e; --muted: #8a8984;
  --problem: #b3261e;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
  --series-4: #eda100; --series-5: #e87ba4; --series-6: #008300;
  --series-7: #6250d6; --series-8: #e34948;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --surface: #1a1a19; --raised: #252523; --border: #3a3936;
    --text: #f0efec; --text-2: #c3c2b7; --muted: #8f8e88;
    --problem: #f2b8b5;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
    --series-4: #c98500; --series-5: #d55181; --series-6: #008300;
    --series-7: #9085e9; --series-8: #e66767;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--surface); color: var(--text);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}
main { max-width: 860px; margin: 0 auto; padding: 16px; }
h1 { margin: 0.5rem 0 0; font-size: 1.6rem; overflow-wrap: anywhere; }
h2 { margin-top: 2.5rem; border-bottom: 1px solid var(--border); }
h3 { font-size: 1rem; overflow-wrap: anywhere; }
h4 { margin: 0 0 0.5rem; font-size: 1rem; }
h5 { margin: 0.75rem 0 0.25rem; font-size: 0.85rem; color: var(--text-2); }
.muted { color: var(--muted); }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.25rem 1rem; }
dt { color: var(--text-2); }
dd { margin: 0; overflow-wrap: anywhere; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { padding: 0.25rem 0.75rem 0.25rem 0; text-align: left; }
th { color: var(--text-2); font-weight: 600; }
tr + tr td { border-top: 1px solid var(--border); }
figure { margin: 1.5rem 0; }
figcaption { font-weight: 600; overflow-wrap: anywhere; }
.chart { width: 100%; height: auto; display: block; }
.chart .grid { stroke: var(--border); stroke-width: 1; }
.chart .tick, .chart .benchmark-label { fill: var(--text-2); font-size: 13px; }
.chart .benchmark { stroke: var(--text-2); stroke-width: 1.5; stroke-dasharray: 5 4; }
.chart .seed { fill: none; stroke: var(--line); stroke-width: 2; }
.chart circle { fill: var(--line); stroke: var(--surface); stroke-width: 2; }
.legend { display: flex; flex-wrap: wrap; gap: 0.25rem 1rem; padding: 0;
  list-style: none; color: var(--text-2); font-size: 0.9rem; }
.swatch { display: inline-block; width: 0.8rem; height: 0.8rem;
  border-radius: 2px; margin-right: 0.35rem; vertical-align: -0.1rem; }
.highlight { border: 1px solid var(--border); border-radius: 8px;
  padding: 0.75rem; margin: 0.75rem 0; }
.tag { display: inline-block; padding: 0 0.4rem; border-radius: 4px;
  background: var(--raised); color: var(--text-2); font-size: 0.8rem;
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }
details.game { border: 1px solid var(--border); border-radius: 8px;
  margin: 0.5rem 0; padding: 0.5rem 0.75rem; }
details.game > summary { cursor: pointer; overflow-wrap: anywhere; }
.round { margin-bottom: 0.75rem; }
.bubble { max-width: 85%; margin: 0.35rem 0; padding: 0.5rem 0.75rem;
  background: var(--raised); border-left: 4px solid var(--firm);
  border-radius: 8px; overflow-wrap: anywhere; }
.bubble.right { margin-left: auto; }
.bubble p { margin: 0; }
.bubble .who { font-size: 0.8rem; color: var(--text-2); }
.scratchpad { margin-top: 0.35rem !important; font-size: 0.9rem;
  font-style: italic; color: var(--text-2); }
.scratchpad::before { content: "thinks: "; font-style: normal; }
.problem { color: var(--problem); font-size: 0.9rem; }
.prices { font-size: 0.9rem; margin-top: 0.25rem; }
"""
