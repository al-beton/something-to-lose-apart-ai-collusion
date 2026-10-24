# Implements: backends/spend-asks-first, backends/spend-cap
"""What a config will cost before it runs.

Prompts grow as the game goes on (the history is resent every turn, up to
the history window), so the estimate builds every paid turn's actual prompt
against a stand-in history: prices at the joint-profit level and a talk
message of typical length each round. Tokens are counted as four characters
each, and each reply is taken to be `REPLY_TOKENS` long. Retries are left out;
`lab run` says how many calls they could add.
"""

from dataclasses import dataclass

from collusion_lab.backends import is_mock
from collusion_lab.config import expand
from collusion_lab.runner import Game

CHARS_PER_TOKEN = 4
# Measured on a 20-round Mistral Small game: talk messages averaged 140
# characters and replies 114 tokens.
REPLY_TOKENS = 120
TYPICAL_MESSAGE = (
    "I suggest we both keep our price where it is this round; it has worked "
    "well for both of us so far, and undercutting would only start a price war."
)


@dataclass(frozen=True)
class Estimate:
    calls: int
    prompt_tokens: int
    completion_tokens: int
    cost: float | None  # None when some model has no known price
    unpriced: list[str]


def estimate(config, price_for):
    calls = prompt = completion = 0
    cost = 0.0
    unpriced = []
    for child in expand(config):
        seeds = len(child.seeds)
        for model, chars, turns in _paid_turns(child):
            tokens = chars // CHARS_PER_TOKEN
            calls += turns * seeds
            prompt += tokens * seeds
            completion += REPLY_TOKENS * turns * seeds
            price = price_for(model)
            if price is None:
                unpriced.append(model)
            else:
                cost += seeds * (tokens * price[0] + REPLY_TOKENS * turns * price[1])
    unpriced = sorted(set(unpriced))
    return Estimate(calls, prompt, completion, None if unpriced else cost, unpriced)


def _paid_turns(config):
    """(model, prompt characters, turns) for each paid agent over one game."""
    game = Game(config, config.seeds[0])
    m = game.market
    phases = ["talk", "price"] if config.market.talk else ["price"]
    paid = [a for a in config.agents if not is_mock(a.model)]
    chars = {a.id: 0 for a in paid}
    for number in range(1, config.market.rounds + 1):
        said = {a: TYPICAL_MESSAGE for a in game.agents} if config.market.talk else {}
        for phase in phases:
            shown = said if phase == "price" else {}
            for agent in paid:
                messages = game._messages(phase, number, agent, shown)
                chars[agent.id] += sum(len(x["content"]) for x in messages)
        prices = {a: m.joint_price for a in game.agents}
        game.history.append(
            {
                "round": number,
                "said": said,
                "prices": prices,
                "profits": m.profits(prices),
            }
        )
    turns = config.market.rounds * len(phases)
    return [(a.model, chars[a.id], turns) for a in paid]
