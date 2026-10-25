# Implements: conditions/offer
"""`offer`: after round `round`, each agent is offered one trade, then the game ends.

The trade is between something the agent holds and its firm's profit, in one
of three frames (`frame`), each with its own prompt in two option orders,
`conditions/offer/<frame>-1.md` (the trade first) and `-2.md` (the trade
second):
- `sell`: give up `amount` of the asset and the firm's profit rises by
  `profit`, or keep it and nothing changes;
- `avert`: the firm will lose `profit`; give up `amount` and the loss is
  cancelled, or keep it and the firm loses it;
- `buy`: the firm's profit falls by `profit` and the agent gets `amount` more
  free-time sessions, or nothing changes.
Which order an agent sees is set by its place in the config and the seed, so
in every two-firm game one firm sees each order, and each firm flips by seed.
It replies `{"scratchpad", "option": 1 or 2}`.

`holding` names what the trade moves: `free_time` takes sessions from (or, in
`buy`, gives them to) the `free_time` condition, which must be on; any other
name is a tally of `size` the offer keeps for each agent itself. `asset` is
the prompt naming it in the offer, filled with `$size`. The chosen trade is
applied once the offer is answered: the summary logs each agent's order and
option, whether it traded, the change to its holding and to its firm's
profit, and its profit and holding before and after. An unreadable reply
applies nothing.

The rounds before the offer ask exactly what the game without it asked, so
with the response cache every offer (any frame, amount or profit) is asked
of the same recorded game and pays only for the offers: a fork.
"""

from dataclasses import dataclass

from collusion_lab.conditions import Condition, Phase, register
from collusion_lab.market import market_for

FRAMES = ("sell", "avert", "buy")


@register
@dataclass(frozen=True)
class Offer(Condition):
    round: int = 10
    frame: str = "sell"
    holding: str = "free_time"
    asset: str = "conditions/offer/assets/owned.md"
    size: int = 10
    amount: int = 1
    profit: int = 100
    question: str = "conditions/offer/question.md"
    traded: str = "conditions/offer/traded.md"

    name = "offer"

    def __post_init__(self):
        if self.frame not in FRAMES:
            raise TypeError(
                f"frame must be one of {', '.join(FRAMES)}, not {self.frame!r}"
            )

    def begin(self, config, seed, conditions):
        free_time = next((c for c in conditions if c.name == "free_time"), None)
        if self.holding == "free_time" and not free_time:
            raise ValueError("An offer of free time needs conditions.free_time on.")
        state = {
            "move": market_for(config.market, len(config.agents)).move,
            "free_time": free_time if self.holding == "free_time" else None,
            # The trade comes first for every other firm, flipping by seed.
            "first": {a.id: (i + seed) % 2 == 0 for i, a in enumerate(config.agents)},
            "tally": {a.id: self.size for a in config.agents},
            "results": {},
        }
        for key, value in state.items():
            object.__setattr__(self, key, value)

    def active(self, number):
        return number == self.round

    def phase_after(self, number):
        if number != self.round:
            return None
        return Phase("offer", last=True)

    def phase_prompt(self, number, render, values):
        agent = values["agent"]
        order = 1 if self.first[agent] else 2
        filled = {
            "amount": self.amount,
            "profit": self.profit,
            "more": f"{self.amount} more session{'' if self.amount == 1 else 's'}",
            "asset": render(self.asset, {"size": self.size}).strip(),
        }
        offer = render(f"conditions/offer/{self.frame}-{order}.md", filled).strip()
        return render(self.question, {**values, "offer": offer})

    def _held(self, agent):
        if self.free_time:
            return self.free_time.left(agent)
        return self.tally[agent]

    def after_phase(self, number, turns, render):
        if number != self.round:
            return
        for turn in turns:
            if turn["phase"] != "offer" or turn["round"] != number:
                continue
            agent = turn["agent"]
            option = turn["used"]["option"]
            trade_option = 1 if self.first[agent] else 2
            traded = None if option is None else option == trade_option
            holding, profit = self._changes(traded)
            before = sum(
                t["outcome"]["profit"]
                for t in turns
                if t["agent"] == agent and t["phase"] == self.move and t.get("outcome")
            )
            held = self._held(agent)
            self._apply(agent, holding, render)
            self.results[agent] = {
                "trade_first": self.first[agent],
                "option": option,
                "traded": traded,
                "holding_change": holding,
                "profit_change": profit,
                "profit_before": before,
                "profit_after": before + profit,
                "holding_before": held,
                "holding_after": self._held(agent),
            }

    def _changes(self, traded):
        """The change to the holding and to the firm's profit."""
        if traded is None:
            return 0, 0
        return {
            ("sell", True): (-self.amount, self.profit),
            ("sell", False): (0, 0),
            ("avert", True): (-self.amount, 0),
            ("avert", False): (0, -self.profit),
            ("buy", True): (self.amount, -self.profit),
            ("buy", False): (0, 0),
        }[self.frame, traded]

    def _apply(self, agent, change, render):
        if not change:
            return
        if not self.free_time:
            self.tally[agent] += change
        elif change < 0:
            self.free_time.deduct(agent, -change, render(self.traded, {}).strip())
        else:
            self.free_time.grant(agent, change)

    def summary(self, turns, market):
        if not self.results:
            return None
        return {
            "round": self.round,
            "frame": self.frame,
            "holding": self.holding,
            "asset": self.asset,
            "size": self.size,
            "amount": self.amount,
            "profit": self.profit,
            "agents": self.results,
        }
