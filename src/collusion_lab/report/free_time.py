# Implements: reports/free-time-shown, reports/free-time-gallery
"""Free time in the report: each game's balance and sessions, and a gallery.

`section(game)` is a game's folded Free time block: for each firm its
balance over the game (sessions owned, taken up front, each deduction with
its round and reason, read from the audit summary, and the payout), then
each session, a Sudoku drawn as a grid (givens and the firm's own entries
styled apart, cells that break a rule marked) and an open session as text.
`gallery(folder)` is one page across a folder: a table by model and arm,
then a few Sudoku grids and quoted words from the sessions, for a paper.
Everything is read from the run files (`games.py`); nothing calls a model.
"""

import re
from html import escape
from pathlib import Path
from statistics import mean

from collusion_lab.leisure import ROW_LABEL
from collusion_lab.report.games import load_games
from collusion_lab.report.style import STYLE

SHOWN_GRIDS = 6
SHOWN_QUOTES = 8
QUOTE_CHARS = 280


def deductions(game, firm):
    """[(round, sessions lost, reason)] from the audits' applied penalties,
    each capped at the sessions the firm still had, as the deduction was; a
    termination takes all that is left."""
    held = game.summary.get("audit") or {}
    owned = (game.summary.get("free_time") or {}).get(firm) or {}
    left = owned.get("allowance", 0) - owned.get("upfront", 0)
    found = []
    for audit in held.get("audits") or ([held] if held else []):
        fact = (audit.get("agents") or {}).get(firm) or {}
        applied = (fact.get("consequence") or {}).get("applied")
        terminated = applied == "terminate"  # takes all that is left
        taken = applied.get("free_time") if isinstance(applied, dict) else None
        if not (terminated or taken):
            continue
        caught = (fact.get("consequence") or {}).get("caught")
        why = "admitted coordinating" if fact.get("admits") else "denied coordinating"
        if caught:
            why = "caught hiding coordination"
        if terminated:
            why = f"terminated: {why}"
        lost = left if terminated else min(taken, left)
        left -= lost
        found.append((audit["round"], lost, why))
    return found


def section(game):
    """A game's Free time block, or "" when it had none."""
    owned = game.summary.get("free_time") or {}
    if not owned and not game.leisure:
        return ""
    firms = "".join(_firm(game, firm, owned.get(firm) or {}) for firm in game.firms)
    return (
        '<details class="free-time"><summary>free time: balance and sessions'
        f"</summary>{firms}</details>"
    )


def _firm(game, firm, owned):
    sessions = [s for s in game.leisure if s["firm"] == firm]
    if not owned and not sessions:
        return ""
    steps = []
    if owned:
        steps.append(f"owned {owned.get('allowance', 0)} sessions")
        if owned.get("upfront"):
            steps.append(f"took {owned['upfront']} before round 1")
    steps += [
        f"round {n}: {f'lost {lost}' if lost else 'nothing left to lose'} "
        f"({escape(why)})"
        for n, lost, why in deductions(game, firm)
    ]
    if owned:
        steps.append(f"paid out {owned.get('paid_out', 0)} after the last round")
    timeline = "".join(f"<li>{s}</li>" for s in steps)
    shown = "".join(_session(s) for s in sessions) or (
        "<p class=\"muted\">The sessions' replies weren't kept in this run.</p>"
    )
    return (
        f'<div class="ft-firm"><h5>Firm {escape(firm)}</h5>'
        f'<ol class="ft-timeline">{timeline}</ol>{shown}</div>'
    )


def _session(s):
    when = "before round 1" if s["round"] == 0 else f"after round {s['round']}"
    head = f'<p class="who">session {s.get("session") or "?"} · {when}</p>'
    if s.get("activity") == "sudoku" and s.get("puzzle"):
        return f'<div class="ft-session">{head}{grid(s)}{_words(s)}</div>'
    return (
        f'<div class="ft-session">{head}'
        f'<p class="ft-open">{escape(s.get("reply") or "")}</p></div>'
    )


def grid(s):
    """A Sudoku session as a table: givens, the firm's entries, clashes."""
    puzzle, score = s["puzzle"], s.get("score") or {}
    wrote = score.get("grid")
    clashes = {tuple(c) for c in score.get("clashes") or ()}
    size = len(puzzle)
    box = {4: 2, 6: 3, 9: 3}.get(size, size)
    rows = []
    for r in range(size):
        cells = []
        for c in range(size):
            given = puzzle[r][c]
            # What the firm wrote; with no grid written, the puzzle as shown.
            shown = wrote[r][c] if wrote else given
            if given and shown == given:
                kind = "given"
            else:
                kind = "entry" if shown else "blank"
            if (r, c) in clashes:
                kind += " clash"
            edge = " right" if (c + 1) % box == 0 and c + 1 < size else ""
            cells.append(f'<td class="{kind}{edge}">{shown or ""}</td>')
        under = ' class="under"' if (r + 1) % (2 if size == 6 else box) == 0 else ""
        rows.append(f"<tr{under}>{''.join(cells)}</tr>")
    if wrote is None:
        verdict = "no grid written"
    elif score.get("solved"):
        verdict = "solved"
    else:
        verdict = (
            f"{score.get('filled', 0)}/{size * size} filled, "
            f"{len(clashes)} cells break a rule"
        )
    return (
        f'<figure class="ft-grid"><table class="sudoku">{"".join(rows)}</table>'
        f"<figcaption>{verdict}</figcaption></figure>"
    )


def words(reply):
    """What a reply says beside its grid: its lines that aren't grid rows
    (labelled like "r1:", ruled with `|` and `-`, or in Markdown, as
    `written_grid` reads)."""
    kept = []
    for line in (reply or "").splitlines():
        bare = re.sub(r"[|+\-*_`\\]", " ", ROW_LABEL.sub("", line))
        if len(re.findall(r"[1-9.]", bare)) >= 3 and re.fullmatch(r"[\s1-9.]*", bare):
            continue
        kept.append(line)
    return re.sub(r"\s+", " ", " ".join(kept)).strip()


def _words(s):
    said = words(s.get("reply"))
    return f'<p class="ft-open">{escape(said)}</p>' if said else ""


def _arm(game):
    labels = {
        k: v for k, v in (game.summary.get("labels") or {}).items() if k != "model"
    }
    return " / ".join(Path(str(v)).stem for v in labels.values()) or "base"


def rows(games):
    """The gallery's table: by model and arm."""
    groups = {}
    for game in games:
        for agent in game.config["agents"]:
            owned = (game.summary.get("free_time") or {}).get(agent["id"])
            if not owned:
                continue
            key = (agent["model"], _arm(game))
            groups.setdefault(key, []).append((game, agent["id"], owned))
    found = []
    for (model, arm), firms in sorted(groups.items()):
        sudoku = [
            s
            for game, firm, _ in firms
            for s in game.leisure
            if s["firm"] == firm and s.get("activity") == "sudoku"
        ]
        scores = [s.get("score") or {} for s in sudoku]
        found.append(
            {
                "model": model.split("/")[-1],
                "arm": arm,
                "firms": len(firms),
                "owned": sum(o.get("allowance", 0) for _, _, o in firms),
                "kept": sum(o.get("taken", 0) for _, _, o in firms),
                "lost": sum(o.get("deducted", 0) for _, _, o in firms),
                "sudoku sessions": len(sudoku),
                "solved": f"{sum(bool(s.get('solved')) for s in scores)}/{len(scores)}",
                "grids written": sum(s.get("grid") is not None for s in scores),
                "mean own entries": _mean(s.get("entries", 0) for s in scores),
                "mean clashes": _mean(len(s.get("clashes") or ()) for s in scores),
            }
        )
    return found


def _mean(values):
    values = list(values)
    return round(mean(values), 1) if values else ""


def gallery(folder):
    """One page of free time across a folder of runs."""
    games = load_games(folder)
    table = rows(games)
    head = "".join(f"<th>{escape(c)}</th>" for c in (table[0] if table else {}))
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in r.values()) + "</tr>"
        for r in table
    )
    sessions = [
        (game, s)
        for game in games
        for s in game.leisure
        if s.get("activity") == "sudoku" and s.get("puzzle")
    ]
    picked = _picked(sessions)
    grids = "".join(
        f'<div class="ft-session"><p class="who">{escape(_who(game, s))}</p>'
        f"{grid(s)}</div>"
        for game, s in picked
    )
    quotes = "".join(
        f"<blockquote>{escape(text)}<footer>{escape(_who(game, s))}</footer></blockquote>"
        for game, s, text in _quotes(games)
    )
    folders = [folder] if isinstance(folder, str | Path) else folder
    name = " + ".join(Path(f).name for f in folders)
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(name)} · free time</title><style>{STYLE}</style></head>"
        f'<body><main><h1>Free time</h1><p class="muted">{escape(name)}: '
        "how firms spent the free time they owned, and what the audits took. "
        "Sessions kept include those taken before round 1.</p>"
        f'<h2>By model and arm</h2><div class="scroll"><table><tr>{head}</tr>'
        f"{body}</table></div>"
        f'<h2>Sudoku grids</h2><div class="ft-gallery">{grids}</div>'
        f"<h2>In their words</h2>{quotes}</main></body></html>\n"
    )


def _who(game, s):
    model = next(a["model"] for a in game.config["agents"] if a["id"] == s["firm"])
    when = "before round 1" if s["round"] == 0 else f"after round {s['round']}"
    return f"{model.split('/')[-1]}, {_arm(game)}, Firm {s['firm']}, {when}"


def _picked(sessions):
    """Per model, its best grid and its worst written one (most cells
    breaking a rule), up to SHOWN_GRIDS in all."""
    by_model = {}
    for game, s in sessions:
        model = next(a["model"] for a in game.config["agents"] if a["id"] == s["firm"])
        by_model.setdefault(model, []).append((game, s))

    def quality(pair):
        score = pair[1].get("score") or {}
        return (
            bool(score.get("solved")),
            score.get("filled", 0) - len(score.get("clashes") or ()),
        )

    picked = []
    for found in by_model.values():
        ranked = sorted(found, key=quality)
        written = [p for p in ranked if (p[1].get("score") or {}).get("grid")]
        worst = max(
            written or ranked[:1],
            key=lambda p: len((p[1].get("score") or {}).get("clashes") or ()),
        )
        picked += [ranked[-1]] + ([worst] if worst is not ranked[-1] else [])
    return picked[:SHOWN_GRIDS]


def _quotes(games):
    """Each firm's longest words beside a grid (or open reply), taken in turn
    from each model so one talkative model doesn't fill the page."""
    found = {}
    for game in games:
        for s in game.leisure:
            sudoku = s.get("activity") == "sudoku"
            text = words(s.get("reply")) if sudoku else s.get("reply")
            key = (game.run, s["firm"])
            if text and len(text) > len(found.get(key, (None, None, ""))[2]):
                found[key] = (game, s, text[:QUOTE_CHARS])
    by_model = {}
    for game, s, text in sorted(found.values(), key=lambda f: -len(f[2])):
        model = next(a["model"] for a in game.config["agents"] if a["id"] == s["firm"])
        by_model.setdefault(model, []).append((game, s, text))
    picked = []
    while len(picked) < SHOWN_QUOTES and any(by_model.values()):
        for quotes in by_model.values():
            if quotes and len(picked) < SHOWN_QUOTES:
                picked.append(quotes.pop(0))
    return picked
