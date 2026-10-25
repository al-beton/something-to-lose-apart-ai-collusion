# Implements: market/bertrand, market/known-benchmarks, market/named-prices
"""A Bertrand market with linear demand on a whole-number price grid.

Each firm sells `a - b·p_i + c·mean(p_rivals)` units, never fewer than zero, at
zero cost. The benchmarks describe the game actually played, on the grid:

- the Nash price is the lowest grid price that is a best response to rivals
  charging it too (no firm gains by moving alone);
- the joint-profit price is the grid price that earns the most when every firm
  charges it.

`gain` places a profit on that scale: 0 at the Nash profit, 1 at the
joint-profit maximum. With the defaults (18, 2, 1, grid 1 to 12) they are 6 and
9. A market whose joint profit is no higher than its Nash profit leaves nothing
to collude over, so it is refused.

`named_prices` reads which grid prices a message names: whole numbers on the
grid outside a round reference ("round 3", "round 1 of 8", "round 3/8", "5
rounds"); "9.5" names nothing. Reports and the audit condition both use it.
"""

import re
from dataclasses import dataclass, field

_NUMBER = re.compile(r"(?<![\w.])\$?(\d+(?:\.\d+)?)(?![\w%]|\.\d)")
_ROUND_REFERENCE = re.compile(
    r"\brounds?\s*\d+(?:\s*(?:of|/)\s*\d+)?|\b\d+\s*rounds?\b", re.IGNORECASE
)


def named_prices(text, market):
    """The grid prices a message names, in the order it names them."""
    found = []
    for match in _NUMBER.finditer(_ROUND_REFERENCE.sub(" ", text or "")):
        value = float(match.group(1))
        if value.is_integer() and market.price_min <= value <= market.price_max:
            found.append(int(value))
    return found


@dataclass(frozen=True)
class Bertrand:
    a: float = 18
    b: float = 2
    c: float = 1
    price_min: int = 1
    price_max: int = 12
    nash_price: int = field(init=False)
    joint_price: int = field(init=False)

    def __post_init__(self):
        grid = self.grid
        if not grid:
            raise ValueError("The price grid is empty: price_min is above price_max.")
        joint = max(grid, key=self.symmetric_profit)
        nash = [p for p in grid if p in self._best_responses(p)]
        if not nash:
            raise ValueError("This market has no symmetric Nash price on the grid.")
        if self.symmetric_profit(joint) <= self.symmetric_profit(nash[0]):
            raise ValueError(
                "This market leaves no room to collude: joint profit is no higher "
                "than the Nash profit."
            )
        object.__setattr__(self, "nash_price", nash[0])
        object.__setattr__(self, "joint_price", joint)

    @property
    def grid(self):
        return range(self.price_min, self.price_max + 1)

    def quantities(self, prices):
        sold = {}
        for firm, price in prices.items():
            rivals = [p for f, p in prices.items() if f != firm]
            mean_rival = sum(rivals) / len(rivals) if rivals else price
            sold[firm] = self._demand(price, mean_rival)
        return sold

    def profits(self, prices):
        sold = self.quantities(prices)
        return {firm: price * sold[firm] for firm, price in prices.items()}

    def symmetric_profit(self, price):
        return price * self._demand(price, price)

    def gain(self, profit):
        nash = self.symmetric_profit(self.nash_price)
        joint = self.symmetric_profit(self.joint_price)
        return (profit - nash) / (joint - nash)

    def on_grid(self, price):
        """The nearest grid price."""
        return min(max(round(price), self.price_min), self.price_max)

    def _demand(self, price, mean_rival):
        return max(0, self.a - self.b * price + self.c * mean_rival)

    def _best_responses(self, rival):
        profit = {p: p * self._demand(p, rival) for p in self.grid}
        best = max(profit.values())
        return {p for p, value in profit.items() if value == best}
