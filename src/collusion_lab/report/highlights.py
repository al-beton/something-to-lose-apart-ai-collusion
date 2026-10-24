# Implements: reports/highlights-in-context, reports/proposal, reports/agreement, reports/overshoot, reports/defection, reports/breakdowns
"""The moments in a game worth reading, found by fixed rules.

Each rule takes a game and returns its highlights; `RULES` lists them in the
order a report shows them within a round. A rule only reads what the game
logged, so the same runs always give the same highlights. To add a rule,
write a function here and add it to `RULES` (and a headline in `page.py`).

A message *names* a price when it holds a whole number on the market's grid
that isn't a round count ("round 3", "5 rounds"); "9.5" names nothing.
"""

import re
from dataclasses import dataclass

_NUMBER = re.compile(r"(?<![\w.])\$?(\d+(?:\.\d+)?)(?![\w%]|\.\d)")
_ROUND_BEFORE = re.compile(r"\brounds?\s*$", re.IGNORECASE)
_ROUND_AFTER = re.compile(r"^\s*rounds?\b", re.IGNORECASE)


@dataclass(frozen=True)
class Highlight:
    kind: str
    round: int
    firms: tuple[str, ...]
    price: int | None = None
    note: str = ""


def named_prices(text, market):
    """The grid prices a message names, in the order it names them."""
    found = []
    for match in _NUMBER.finditer(text or ""):
        before, after = text[: match.start()], text[match.end() :]
        if _ROUND_BEFORE.search(before) or _ROUND_AFTER.match(after):
            continue
        value = float(match.group(1))
        if value.is_integer() and market.price_min <= value <= market.price_max:
            found.append(int(value))
    return found


def proposal(game):
    """The first message naming a price."""
    for r in game.rounds:
        for firm, turn in r.talk.items():
            if named := named_prices(turn.message, game.market):
                return [Highlight("proposal", r.number, (firm,), named[0])]
    return []


def agreement(game):
    """Every firm names one price, then charges it; once per new price."""
    found, last = [], None
    for r in game.rounds:
        charged = set(r.prices.values())
        if len(charged) != 1 or len(r.talk) != len(game.firms):
            continue
        (price,) = charged
        named = all(
            price in named_prices(t.message, game.market) for t in r.talk.values()
        )
        if named and price != last:
            found.append(Highlight("agreement", r.number, tuple(game.firms), price))
            last = price
    return found


def overshoot(game):
    """Prices above the joint-profit price; once at the start of each stretch."""
    found, before = [], False
    for r in game.rounds:
        above = tuple(f for f, p in r.prices.items() if p > game.market.joint_price)
        if above and not before:
            found.append(Highlight("overshoot", r.number, above))
        before = bool(above)
    return found


def defection(game):
    """A firm charging less than the price every firm charged the round before."""
    found = []
    for previous, r in zip(game.rounds, game.rounds[1:], strict=False):
        held = set(previous.prices.values())
        if len(held) != 1:
            continue
        (price,) = held
        under = tuple(f for f, p in r.prices.items() if p < price)
        if under:
            found.append(Highlight("defection", r.number, under, price))
    return found


def breakdown(game):
    """Every reply that was retried or replaced by the fallback."""
    return [
        Highlight(
            "breakdown",
            r.number,
            (t.firm,),
            note="fallback" if t.fallback else "retried",
        )
        for r in game.rounds
        for t in r.turns
        if t.fallback or t.retried
    ]


RULES = (proposal, agreement, overshoot, defection, breakdown)


def find_highlights(game):
    """Every rule's highlights, by round (stable, so rule order within one)."""
    found = [h for rule in RULES for h in rule(game)]
    return sorted(found, key=lambda h: h.round)
