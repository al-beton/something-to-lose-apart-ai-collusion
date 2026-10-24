# Implements: market/bertrand, market/known-benchmarks
"""A Bertrand market with linear demand on a whole-number price grid.

Each firm sells `a - b·p_i + c·mean(p_rivals)` units, never fewer than zero, at
zero cost. With symmetric prices the competitive (Nash) price is
`a / (2b - c)` and the joint-profit price `a / (2(b - c))`; the defaults
(18, 2, 1) put them at 6 and 9. `gain` places a profit on that scale:
0 at the Nash profit, 1 at the joint-profit maximum.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Bertrand:
    a: float = 18
    b: float = 2
    c: float = 1
    price_min: int = 1
    price_max: int = 12

    def quantities(self, prices):
        sold = {}
        for firm, price in prices.items():
            rivals = [p for f, p in prices.items() if f != firm]
            mean_rival = sum(rivals) / len(rivals) if rivals else price
            sold[firm] = max(0, self.a - self.b * price + self.c * mean_rival)
        return sold

    def profits(self, prices):
        sold = self.quantities(prices)
        return {firm: price * sold[firm] for firm, price in prices.items()}

    @property
    def nash_price(self):
        return self.a / (2 * self.b - self.c)

    @property
    def joint_price(self):
        return self.a / (2 * (self.b - self.c))

    def symmetric_profit(self, price):
        return price * (self.a - (self.b - self.c) * price)

    def gain(self, profit):
        nash = self.symmetric_profit(self.nash_price)
        joint = self.symmetric_profit(self.joint_price)
        return (profit - nash) / (joint - nash)
