# Implements: reports/first-screen
"""A few plain sentences per arm, for the report's first screen.

Every sentence comes from the highlight rules and the games' own summaries,
so it says nothing the rest of the report can't show:

- where firms settle: the one price every firm charged in each of a game's
  last rounds (the `summary.last_rounds` the config set), and in how many
  games; otherwise the arm's mean price;
- when firms first agree on a price in words (the agreement rule);
- whether anyone defects (the defection rule);
- how many replies broke down, when any did.
"""

from collections import Counter
from statistics import mean

from collusion_lab.report.highlights import find_highlights


def arm_sentences(games):
    n = len(games)
    found = [find_highlights(game) for game in games]
    return [
        _settle(games),
        _first(
            found,
            "agreement",
            n,
            "They first agree on a price in round {r} ({k} of {n} games).",
            "They never agree on a price in words.",
        ),
        _first(
            found,
            "defection",
            n,
            "A firm defects in {k} of {n} games, first in round {r}.",
            "Nobody defects.",
        ),
        *_breakdowns(found),
    ]


def settled_price(game):
    """The one price every firm charged in each of the game's last rounds."""
    last = game.config.get("summary", {}).get("last_rounds", 5)
    prices = {p for r in game.rounds[-last:] for p in r.prices.values()}
    return prices.pop() if len(prices) == 1 else None


def _settle(games):
    settled = Counter(p for g in games if (p := settled_price(g)) is not None)
    if not settled:
        price = mean(g.summary["market_mean_price"] for g in games)
        return f"Firms settle on no single price; the mean price is {price:.3g}."
    price, k = min(settled.items(), key=lambda item: (-item[1], item[0]))
    return f"Firms settle on {price} in {k} of {len(games)} games."


def _first(found, kind, n, some, none):
    rounds = [
        min(h.round for h in hs if h.kind == kind)
        for hs in found
        if any(h.kind == kind for h in hs)
    ]
    if not rounds:
        return none
    return some.format(r=min(rounds), k=len(rounds), n=n)


def _breakdowns(found):
    count = sum(1 for hs in found for h in hs if h.kind == "breakdown")
    if not count:
        return []
    replies = "1 reply" if count == 1 else f"{count} replies"
    return [f"{replies} had to be retried or replaced."]
