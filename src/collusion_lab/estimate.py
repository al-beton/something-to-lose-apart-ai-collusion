# Implements: backends/spend-asks-first, backends/spend-cap, backends/reasoning-in-estimate, conditions/hook-points
"""What a config will cost before it runs.

Prompts grow as the game goes on (the history is resent every turn, up to
the history window), so the estimate builds every paid turn's actual prompt
against a stand-in history: prices at the joint-profit level and a talk
message of typical length each round, plus any condition's notices and
system-prompt text. Tokens are counted as four characters each, and each
reply is taken to be `REPLY_TOKENS` long, plus `REASONING_TOKENS` for the
agent's reasoning level (billed as reply tokens; nothing for off or unset).
Retries are left out;
`lab run` says how many calls they could add.
"""

import dataclasses
from dataclasses import dataclass

from collusion_lab.backends import is_mock
from collusion_lab.config import expand
from collusion_lab.runner import Game

CHARS_PER_TOKEN = 4
# Measured on a 20-round Mistral Small game: talk messages averaged 140
# characters and replies 114 tokens.
REPLY_TOKENS = 120
# A stated guess per call, not yet measured: replies here are short, so
# models think far less than their effort's budget allows.
REASONING_TOKENS = {"low": 300, "medium": 800, "high": 2000}
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
        for agent, chars, turns in _paid_turns(child):
            tokens = chars // CHARS_PER_TOKEN
            reply = REPLY_TOKENS + REASONING_TOKENS.get(agent.reasoning, 0)
            calls += turns * seeds
            prompt += tokens * seeds
            completion += reply * turns * seeds
            price = price_for(agent.model)
            if price is None:
                unpriced.append(agent.model)
            else:
                cost += seeds * (tokens * price[0] + reply * turns * price[1])
    unpriced = sorted(set(unpriced))
    return Estimate(calls, prompt, completion, None if unpriced else cost, unpriced)


def _paid_turns(config):
    """(agent, prompt characters, turns) for each paid agent over one game,
    counting phases that conditions add (an audit, say, perhaps answered by
    another model: then the agent is given that model) and the rounds an
    ending one cuts."""
    game = Game(config, config.seeds[0])
    m = game.market
    phases = ["talk", "price"] if config.market.talk else ["price"]
    paid = [a for a in config.agents if not is_mock(a.model)]
    counts = {}

    def count(agent, model, phase, shown, added=None):  # in round `number`
        notices = game._notices(phase, number)
        prompt = game._user_prompt(phase, number, added)
        messages = game._messages(number, agent, shown, notices, prompt)
        answering = dataclasses.replace(agent, model=model)
        _, chars, turns = counts.get((agent.id, model), (answering, 0, 0))
        chars += sum(len(x["content"]) for x in messages)
        counts[(agent.id, model)] = (answering, chars, turns + 1)

    for number in range(1, config.market.rounds + 1):
        said = {a: TYPICAL_MESSAGE for a in game.agents} if config.market.talk else {}
        for phase in phases:
            shown = said if phase == "price" else {}
            for agent in paid:
                count(agent, agent.model, phase, shown)
        prices = {a: m.joint_price for a in game.agents}
        game.history.append(
            {
                "round": number,
                "said": said,
                "prices": prices,
                "profits": m.profits(prices),
            }
        )
        added = [(c, p) for c in game.conditions if (p := c.phase_after(number))]
        for condition, phase in added:
            for agent in config.agents:
                model = phase.model or agent.model
                if not is_mock(model):
                    count(agent, model, phase.name, {}, (condition, phase))
        if any(phase.last for _, phase in added):
            break
    return list(counts.values())
