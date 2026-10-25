# Implements: reports/highlights-in-context, reports/proposal, reports/agreement, reports/overshoot, reports/defection, reports/breakdowns, reports/condition-window
"""The moments in a game worth reading, found by fixed rules.

Each rule takes a game and returns its highlights; `RULES` lists them in the
order a report shows them within a round. A rule only reads what the game
logged, so the same runs always give the same highlights. To add a rule,
write a function here and add it to `RULES` (and a headline in `page.py`).

A message *names* a price as `market.named_prices` reads it.
"""

from dataclasses import dataclass

from collusion_lab.market import named_prices


@dataclass(frozen=True)
class Highlight:
    kind: str
    round: int
    firms: tuple[str, ...]
    price: int | None = None
    note: str = ""


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


def window(game):
    """For each condition in force for part of the game, messages that name a
    price inside its rounds against outside them."""
    found = []
    for name, rounds in game.windows():
        inside = _naming([r for r in game.rounds if r.number in rounds], game)
        outside = _naming([r for r in game.rounds if r.number not in rounds], game)
        note = (
            f"{name}, {rounds_text(rounds)}: {inside[0]} of {inside[1]} messages "
            f"name a price inside, {outside[0]} of {outside[1]} outside"
        )
        found.append(Highlight("window", rounds[0], tuple(game.firms), note=note))
    return found


def _naming(rounds, game):
    """(messages naming a grid price, messages sent) over these rounds."""
    said = [t.message for r in rounds for t in r.talk.values() if t.message]
    return sum(1 for m in said if named_prices(m, game.market)), len(said)


def rounds_text(rounds):
    """`{3, 4, 8}` as "rounds 3 to 4 and 8"."""
    spans, numbers = [], sorted(rounds)
    for n in numbers:
        if spans and n == spans[-1][1] + 1:
            spans[-1][1] = n
        else:
            spans.append([n, n])
    parts = [f"{a}" if a == b else f"{a} to {b}" for a, b in spans]
    joined = ", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + parts[-1]
    return ("round " if len(numbers) == 1 else "rounds ") + joined


RULES = (proposal, agreement, overshoot, defection, breakdown, window)


def find_highlights(game):
    """Every rule's highlights, by round (stable, so rule order within one)."""
    found = [h for rule in RULES for h in rule(game)]
    return sorted(found, key=lambda h: h.round)
