# Implements: reports/reasoning-folded, reports/one-page, reports/header, reports/first-screen, reports/contents-bar, reports/setup, reports/summary, reports/price-chart, reports/arm-tabs, reports/highlights-in-context, reports/transcripts, reports/self-contained, runs/fallback-rates, runs/missing-runs-shown, reports/condition-window
"""The report page: one self-contained HTML file, read from the top down.

A sticky contents bar, then:

1. the header: the folder's name and one line of games, arms, calls and cost;
2. the summary (the first screen): a few sentences per arm (`overview.py`),
   the `lab summary` table and one small bar chart of every arm's mean price,
   then the unreadable replies by model and any flagged runs, and the runs
   that failed or never finished, each when there are any;
3. Setup, folded away: what was run and exactly what agents were told
   (`told.py`);
4. the charts: one per arm, side by side on the same axes;
5. the arms, one tab each: highlights grouped by kind and folded to their
   headlines, then each game as a card with a strip of its rounds; a round
   shows any notice its firms saw above what they said.

An arm is a group of `group_runs` (the swept values). Everything is inline,
with no script (`style.py` explains the tabs and folding), so the page opens
with no network. Everything a run logged is escaped, since models write what
they like.
"""

from html import escape
from pathlib import Path
from statistics import mean

from collusion_lab.report.chart import (
    legend,
    line_names,
    overview_chart,
    price_chart,
    series_colour,
)
from collusion_lab.report.games import load_game
from collusion_lab.report.highlights import find_highlights, rounds_text
from collusion_lab.report.overview import arm_sentences
from collusion_lab.report.style import STYLE, tab_rules
from collusion_lab.report.told import (
    round_conditions,
    round_notices,
    what_agents_were_told,
)
from collusion_lab.summary import (
    FLAG_RATE,
    cell,
    flagged_runs,
    group_runs,
    missing_runs,
    reply_rates,
    run_cost,
    spent,
    summarize,
)

HEADLINES = {
    "proposal": "{who} proposes {price}",
    "agreement": "{who} agree on {price} and charge it",
    "overshoot": "{who} price above the joint-profit price",
    "defection": "{who} undercut {price}, which every firm charged the round before",
    "breakdown": "{who}'s reply broke down ({note})",
    "window": "{note}",
}
KINDS = {
    "proposal": "Proposals",
    "agreement": "Agreements",
    "overshoot": "Overshoots",
    "defection": "Defections",
    "breakdown": "Breakdowns",
    "window": "Condition windows",
}
SHOWN = 5
CONTENTS = {
    "summary": "Summary",
    "setup": "What agents were told",
    "charts": "Charts",
    "arms": "Arms",
}


def build_report(folder):
    folder = Path(folder)
    arms = load_arms(folder)
    games = [g for _, _, gs in arms for g in gs]
    title = f"{folder.name} · collusion-lab report"
    links = "".join(f'<a href="#{k}">{v}</a>' for k, v in CONTENTS.items())
    body = [
        _header(folder.name, games, arms, spent(folder)),
        _summary(folder, arms),
        _replies(folder),
        _missing(folder),
        _setup(games, arms),
        _charts(arms),
        _arm_tabs(arms),
    ]
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(title)}</title>"
        f"<style>{STYLE}{tab_rules(len(arms))}</style></head>"
        f'<body><nav class="contents">{links}</nav>'
        f"<main>{''.join(body)}</main></body></html>\n"
    )


def load_arms(folder):
    """(name, caption, games) for each group of runs, in table order.

    The name is brief: each swept value cut to its last `/` part when that
    still tells the arms apart (`openrouter/openai/gpt-4.1-mini` is
    `gpt-4.1-mini`). The caption names every value in full.
    """
    by, groups = group_runs(folder)
    briefs = [_brief([key[d] for key, _ in groups]) for d in range(len(by))]
    arms = []
    for i, (key, runs) in enumerate(groups):
        played = [r for r in runs if r.summary]  # missing runs have no game
        if not played:
            continue
        games = sorted(
            (load_game(r.dir) for r in played), key=lambda g: (g.seed, g.run)
        )
        name = ", ".join(brief[i] for brief in briefs) or "All runs"
        caption = ", ".join(f"{k} = {cell(v)}" for k, v in zip(by, key, strict=True))
        arms.append((name, caption or "All runs", games))
    return arms


def _brief(values):
    full = [cell(v) for v in values]
    last = [v.rsplit("/", 1)[-1] for v in full]
    return last if len(set(last)) == len(set(full)) else full


def _where(names, arms):
    """Which arms a text was seen in: "every arm", or their names."""
    if len(names) == len(arms):
        return "every arm"
    return ", ".join(names)


def _header(name, games, arms, manifests):
    count = f"{len(arms)} arm" + ("" if len(arms) == 1 else "s")
    line = f"{len(games)} games in {count} · {_spend(manifests)}"
    return (
        f'<section id="header"><h1>{escape(name)}</h1>'
        f'<p class="lede">{escape(line)}</p></section>'
    )


def _spend(manifests):
    calls = sum(m.get("calls", 0) for m in manifests)
    unpriced = sum(m.get("unpriced_calls", 0) for m in manifests)
    if any(m.get("cost") is None for m in manifests):
        return f"{calls} calls, cost unknown ({unpriced} calls unpriced)"
    return f"{calls} calls, cost ${sum(run_cost(m) for m in manifests):.4f}"


def _replies(folder):
    rates = reply_rates(folder)
    if not any(r["unreadable"] for r in rates):
        return ""
    head = "".join(f"<th>{escape(c)}</th>" for c in rates[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(cell(v))}</td>" for v in r.values()) + "</tr>"
        for r in rates
    )
    flags = "".join(
        f"<li><code>{escape(f['run'])}</code>: {f['fallback rate']:.0%} of turns "
        f"fell back ({escape(f['reasons'])})</li>"
        for f in flagged_runs(folder)
    )
    if flags:
        flags = (
            f"<p>Runs where more than {FLAG_RATE:.0%} of turns fell back:</p>"
            f"<ul>{flags}</ul>"
        )
    return (
        '<section id="replies"><h2>Unreadable replies</h2>'
        '<p class="muted">Replies the game couldn\'t read, on either attempt, and '
        "the turns that fell back to a default.</p>"
        f'<div class="scroll"><table><tr>{head}</tr>{body}</table></div>'
        f"{flags}</section>"
    )


def _summary(folder, arms):
    notes = "".join(
        f'<li class="arm-note"><b>{escape(name)}</b>: '
        f"{escape(' '.join(arm_sentences(games)))}</li>"
        for name, _, games in arms
        if games
    )
    rows = summarize(folder)
    if not rows:
        return '<section id="summary"><h2>Summary</h2><p>No runs found.</p></section>'
    head = "".join(f"<th>{escape(c)}</th>" for c in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(cell(v))}</td>" for v in r.values()) + "</tr>"
        for r in rows
    )
    # One overview per market: grids and benchmarks differ, so an arm that
    # played in several markets gets a bar in each.
    markets = {}
    for name, _, games in arms:
        for market in dict.fromkeys(g.market for g in games):
            prices = [
                g.summary["market_mean_price"] for g in games if g.market == market
            ]
            markets.setdefault(market, []).append((name, mean(prices)))
    charts = "".join(
        "<figure>"
        + (f"<figcaption>{escape(_market(m))}</figcaption>" if len(markets) > 1 else "")
        + f"{overview_chart(bars, m)}</figure>"
        for m, bars in markets.items()
    )
    return (
        '<section id="summary"><h2>Summary</h2>'
        f'<ul class="arm-notes">{notes}</ul>'
        f'<div class="scroll"><table><tr>{head}</tr>{body}</table></div>'
        '<p class="muted">Mean price and gain over each run\'s last rounds; '
        "gain is 0 at the Nash profit and 1 at the joint-profit maximum.</p>"
        f"{charts}</section>"
    )


def _missing(folder):
    missing = missing_runs(folder)
    if not missing:
        return ""
    items = "".join(
        f"<li><code>{escape(m['run'])}</code> {escape(m['state'])}"
        + (f": {escape(m['error'])}" if m["error"] else "")
        + "</li>"
        for m in missing
    )
    return (
        '<section id="missing"><h2>Missing runs</h2>'
        '<p class="muted">Planned runs that failed or never finished; the '
        f"summary leaves them out.</p><ul>{items}</ul></section>"
    )


def _setup(games, arms):
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
        "Market": "; ".join(_market(m) for m in markets),
    }
    dl = "".join(f"<dt>{k}</dt><dd>{escape(v)}</dd>" for k, v in facts.items())
    found = what_agents_were_told([(n, gs) for n, _, gs in arms])
    systems, phases, conditions, extras = found
    told = ["<h3>System prompts</h3>"]
    told += [
        f'<p class="muted">Used in {escape(_where(s.arms, arms))}.</p>'
        f'<pre class="prompt">{escape(s.text)}</pre>'
        for s in systems
    ]
    told.append(
        "<h3>Phase prompts</h3>"
        '<p class="muted">As the first firm saw them in round 1; later rounds '
        "add the history so far.</p>"
    )
    told += [
        f'<h4>{phase}</h4><pre class="prompt">{escape(text)}</pre>'
        for phase, text in phases
    ]
    if conditions:
        told.append("<h3>Conditions</h3><ul>")
        told += [
            f"<li><b>{escape(c.text)}</b>: in force in {rounds_text(c.rounds)}, "
            f"in {escape(_where(c.arms, arms))}.</li>"
            for c in conditions
        ]
        told.append("</ul>")
    told.append("<h3>Other text in their prompts</h3>")
    told += [
        f'<p class="muted">Seen in {rounds_text(e.rounds)}, in '
        f'{escape(_where(e.arms, arms))}.</p><pre class="prompt">{escape(e.text)}</pre>'
        for e in extras
    ] or ["<p>None: every prompt was the usual one.</p>"]
    return (
        '<section id="setup"><details class="setup">'
        "<summary><h2>What agents were told</h2></summary>"
        f"<dl>{dl}</dl>{''.join(told)}</details></section>"
    )


def _market(m):
    return (
        f"Nash price {m.nash_price}, joint-profit price {m.joint_price} "
        f"(prices {m.price_min} to {m.price_max})"
    )


def _charts(arms):
    rounds = max((len(g.rounds) for _, _, gs in arms for g in gs), default=1)
    figures = []
    for _, caption, games in arms:
        # An arm can hold games from several markets when the market isn't
        # swept; each gets its own chart, since grids and benchmarks differ.
        markets = {}
        for game in games:
            markets.setdefault(game.market, []).append(game)
        for market, same in markets.items():
            label = caption + (f" ({_market(market)})" if len(markets) > 1 else "")
            figures.append(
                f"<figure><figcaption>{escape(label)}</figcaption>"
                f"{price_chart(same, market, rounds)}"
                f"{legend(line_names(same))}</figure>"
            )
    return (
        '<section id="charts"><h2>Prices over rounds</h2>'
        '<p class="muted">Mean price each round, one line per seed, on the same '
        "axes for every arm; dashed lines mark the Nash and joint-profit prices.</p>"
        f'<div class="compare">{"".join(figures)}</div></section>'
    )


def _arm_tabs(arms):
    tabs, labels, panels = [], [], []
    start = 0
    for i, (name, _, games) in enumerate(arms):
        checked = " checked" if i == 0 else ""
        tabs.append(
            f'<input type="radio" name="arm" class="tab" id="arm-{i}"{checked}>'
        )
        labels.append(f'<label for="arm-{i}">{escape(name)}</label>')
        panels.append(
            f'<div class="panel" id="panel-{i}"><h3>Highlights</h3>'
            f"{_highlights(games)}<h3>Games</h3>"
            f"{''.join(_game(g, start + j) for j, g in enumerate(games))}</div>"
        )
        start += len(games)
    if len(arms) == 1:
        tabs, labels = [], []
    return (
        '<section id="arms"><h2>Arms</h2>'
        '<p class="muted">Highlights are found by fixed rules, each shown with the '
        "round before it. Scratchpads are private notes rivals never saw.</p>"
        f'{"".join(tabs)}<div class="tabs">{"".join(labels)}</div>'
        f'<div class="panels">{"".join(panels)}</div></section>'
    )


def _highlights(games):
    by_kind = {kind: [] for kind in KINDS}
    for game in games:
        for h in find_highlights(game):
            by_kind[h.kind].append(_highlight(game, h))
    groups = []
    for kind, found in by_kind.items():
        if not found:
            continue
        more = ""
        if len(found) > SHOWN:
            more = (
                f'<details class="more"><summary>Show all {len(found)}</summary>'
                f"{''.join(found[SHOWN:])}</details>"
            )
        groups.append(
            f'<details class="kind" data-kind="{kind}"><summary>'
            f"{KINDS[kind]} ({len(found)})</summary>"
            f"{''.join(found[:SHOWN])}{more}</details>"
        )
    return "".join(groups) or "<p>Nothing stood out.</p>"


def headline(h):
    """A highlight in one plain sentence: "Firm A proposes 9"."""
    who = ("Firm " if len(h.firms) == 1 else "Firms ") + " and ".join(h.firms)
    return HEADLINES[h.kind].format(who=who, price=h.price, note=h.note)


def _highlight(game, h):
    headline_text = headline(h)
    context = [game.round(h.round - 1), game.round(h.round)]
    rounds = "".join(_round(game, r) for r in context if r)
    return (
        f'<details class="highlight" data-kind="{h.kind}"><summary>'
        f'<span class="tag">{h.kind}</span> Round {h.round}: {escape(headline_text)} '
        f'<span class="muted">{escape(game.run)}</span></summary>{rounds}</details>'
    )


def _game(game, index):
    s = game.summary
    gid = f"g{index}"
    kinds = {}
    for h in find_highlights(game):
        kinds.setdefault(h.round, set()).add(h.kind)
    chips = "".join(
        f'<a class="chip" href="#{gid}-r{r.number}" '
        f'data-kinds="{" ".join(sorted(kinds.get(r.number, ())))}" '
        f'title="Round {r.number}">{"·".join(str(p) for p in r.prices.values())}</a>'
        for r in game.rounds
    )
    rounds = "".join(_round(game, r, f"{gid}-r{r.number}") for r in game.rounds)
    return (
        f'<article class="game" id="{gid}">'
        f'<input type="checkbox" class="game-all" id="{gid}-all">'
        f'<div class="game-head"><b>{escape(game.run)}</b><span class="muted">'
        f"mean price {s['market_mean_price']:g}, gain {s['market_gain']:.3f}"
        f'</span><label for="{gid}-all"><span class="show">whole game</span>'
        '<span class="hide">fold</span></label></div>'
        f'<nav class="strip">{chips}</nav><div class="rounds">{rounds}</div>'
        "</article>"
    )


def _round(game, r, anchor=None):
    side = {firm: i for i, firm in enumerate(game.firms)}
    talk = "".join(_bubble(t, side[t.firm]) for t in r.talk.values())
    thoughts = "".join(
        _bubble(t, side[t.firm])
        for t in r.price.values()
        if t.scratchpad or t.reasoning or t.error or t.retried
    )
    prices = "".join(
        f"<tr><td>Firm {escape(t.firm)}</td><td>{t.price}</td>"
        f"<td>{t.profit:g}</td></tr>"
        for t in r.price.values()
    )
    where = f' id="{anchor}"' if anchor else ""
    notices = "".join(
        f'<p class="notice">{escape(text)}</p>' for text in round_notices(game, r)
    )
    if active := round_conditions(r):
        in_force = escape(", ".join(active))
        notices = f'<p class="conditions">in force: {in_force}</p>{notices}'
    return (
        f'<div class="round"{where}><h5>Round {r.number}</h5>{notices}{talk}{thoughts}'
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
    if turn.reasoning:
        notes.append(
            '<details class="reasoning"><summary>model reasoning</summary>'
            f"<p>{escape(turn.reasoning)}</p></details>"
        )
    if turn.fallback:
        notes.append(f'<p class="problem">fallback: {escape(turn.error)}</p>')
    elif turn.retried:
        notes.append('<p class="problem">retried once</p>')
    return (
        f'<div class="bubble {where}" style="--firm: {series_colour(index)}">'
        f'<p class="who">Firm {escape(turn.firm)} · {turn.phase}</p>'
        f"<p>{text}</p>{''.join(notes)}</div>"
    )
