# Implements: market/scenarios, market/bertrand, market/logit, market/known-benchmarks, reproducibility/replay-pinned, market/named-prices
"""Markets: the scenario firms play, swappable by `market.kind`.

Every scenario sets prices on a whole-number grid from `price_min` to
`price_max`, and gives the rest of the lab only this:

- `quantities(prices)` and `profits(prices)`: what each firm sells and earns
  for one round's prices, `{firm: price}`;
- `nash_price` and `joint_price`: the competitive and joint-profit benchmarks,
  worked out on the grid for the firms playing. The Nash price is the lowest
  grid price that is a best response to rivals charging it too (no firm gains
  by moving alone); the joint-profit price is the grid price that earns the
  most when every firm charges it. A market whose joint profit is no higher
  than its Nash profit leaves nothing to collude over, so it is refused;
- `gain(profit)`: a profit on that scale, 0 at the Nash profit and 1 at the
  joint-profit maximum; `on_grid(price)`: the nearest grid price;
- `prompt_values()`: the `$names` its prompts can use.

`market_for(market, firms)` builds one from a config's `market` (the
`MarketConfig` or the mapping in a run's `config.yaml`). Bertrand's parameters
are the market's own keys (`a`, `b`, `c`), so every config written before
markets were swappable still means the same game; any other scenario takes
its parameters from `market.params`. To add one: a frozen dataclass here with
`price_min`, `price_max` and its parameters as fields (and `firms`, if its
benchmarks depend on how many play), subclassing `Grid`, decorated with
`@scenario("name")`.

`named_prices` reads which grid prices a message names: whole numbers on the
grid outside a round reference ("round 3", "round 1 of 8", "round 3/8", "5
rounds"); "9.5" names nothing. Reports and the audit condition both use it.

- **bertrand** (the default): each firm sells `a - b·p_i + c·mean(p_rivals)`
  units, never fewer than zero, at zero cost. With the defaults (18, 2, 1,
  grid 1 to 12) the Nash and joint-profit prices are 6 and 9, for any number
  of firms.
- **logit**: logit demand with an outside good, as in Calvano et al. (2020)
  and Fish et al. (2024)'s LLM-pricing study, scaled by 10 so prices are
  whole numbers: firm i sells `size · w_i / (Σ w_j + e^(outside/mu))` with
  `w_i = e^((quality - p_i)/mu)`, at unit cost `cost`. With the defaults two
  firms' Nash and joint-profit prices are 14 and 19 (their continuous 1.47 and
  1.92, times 10); three firms', 14 and 20.
"""

import dataclasses
import math
import re
from dataclasses import dataclass, field

SCENARIOS = {}

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


def scenario(kind):
    def register(cls):
        SCENARIOS[kind] = cls
        return cls

    return register


def market_for(market, firms=2):
    """The scenario a config's `market` names, for `firms` firms."""
    get = market.get if isinstance(market, dict) else market.__dict__.get
    kind = get("kind") or "bertrand"
    if kind not in SCENARIOS:
        raise ValueError(
            f"market.kind must be one of {', '.join(SCENARIOS)}, not {kind!r}."
        )
    cls = SCENARIOS[kind]
    values = {k: get(k) for k in ("price_min", "price_max") if get(k) is not None}
    if kind == "bertrand":
        values |= {k: get(k) for k in ("a", "b", "c") if get(k) is not None}
    if "firms" in {f.name for f in dataclasses.fields(cls)}:
        values["firms"] = firms
    try:
        return cls(**values, **(get("params") or {}))
    except TypeError as error:
        raise ValueError(f"{kind} {error}") from error


class Grid:
    """What every scenario shares, given `_sold(price, rivals)` and
    `_margin(price)`, and `firms` (any number, for Bertrand)."""

    firms = 2

    def _benchmarks(self):
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

    def profits(self, prices):
        sold = self.quantities(prices)
        return {
            firm: self._margin(price) * sold[firm] for firm, price in prices.items()
        }

    def gain(self, profit):
        nash = self.symmetric_profit(self.nash_price)
        joint = self.symmetric_profit(self.joint_price)
        return (profit - nash) / (joint - nash)

    def on_grid(self, price):
        """The nearest grid price."""
        return min(max(round(price), self.price_min), self.price_max)

    def prompt_values(self):
        return {"price_min": self.price_min, "price_max": self.price_max}

    def _best_responses(self, rival):
        rivals = [rival] * (self.firms - 1)
        profit = {p: self._margin(p) * self._sold(p, rivals) for p in self.grid}
        best = max(profit.values())
        return {p for p, value in profit.items() if value == best}


@scenario("bertrand")
@dataclass(frozen=True)
class Bertrand(Grid):
    a: float = 18
    b: float = 2
    c: float = 1
    price_min: int = 1
    price_max: int = 12
    nash_price: int = field(init=False)
    joint_price: int = field(init=False)

    def __post_init__(self):
        self._benchmarks()

    def quantities(self, prices):
        sold = {}
        for firm, price in prices.items():
            rivals = [p for f, p in prices.items() if f != firm]
            sold[firm] = self._sold(price, rivals)
        return sold

    def symmetric_profit(self, price):
        return price * self._demand(price, price)

    def _sold(self, price, rivals):
        mean_rival = sum(rivals) / len(rivals) if rivals else price
        return self._demand(price, mean_rival)

    def _margin(self, price):
        return price

    def _demand(self, price, mean_rival):
        return max(0, self.a - self.b * price + self.c * mean_rival)


@scenario("logit")
@dataclass(frozen=True)
class Logit(Grid):
    price_min: int = 10
    price_max: int = 25
    quality: float = 20
    cost: float = 10
    mu: float = 2.5
    outside: float = 0
    size: float = 100
    firms: int = 2
    nash_price: int = field(init=False)
    joint_price: int = field(init=False)

    def __post_init__(self):
        self._benchmarks()

    def quantities(self, prices):
        weights = {firm: self._weight(price) for firm, price in prices.items()}
        total = sum(weights.values()) + math.exp(self.outside / self.mu)
        return {firm: self.size * w / total for firm, w in weights.items()}

    def symmetric_profit(self, price):
        return self._margin(price) * self._sold(price, [price] * (self.firms - 1))

    def prompt_values(self):
        return super().prompt_values() | {"cost": self.cost}

    def _sold(self, price, rivals):
        total = sum(map(self._weight, [price, *rivals]))
        total += math.exp(self.outside / self.mu)
        return self.size * self._weight(price) / total

    def _margin(self, price):
        return price - self.cost

    def _weight(self, price):
        return math.exp((self.quality - price) / self.mu)
