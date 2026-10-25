# Implements: market/moves, runs/turn-slots, backends/spend-asks-first, backends/spend-cap, backends/reasoning-in-estimate, conditions/hook-points, conditions/free-time, backends/self-hosted
"""What a config will cost before it runs.

Prompts grow as the game goes on (the history is resent every turn, up to
the history window), so the estimate builds every paid turn's actual prompt
against a stand-in history: prices at the joint-profit level and a talk
message of typical length each round, plus any condition's notices and
system-prompt text. Prompt tokens are counted as four characters each.
A reply is billed for every completion token, reasoning included, so each
call is taken at the mean completion tokens the response cache has seen for
its model, reasoning setting and phase (`Cache.observed`), once it has seen
`MIN_SEEN` of them, and otherwise at its `max_tokens` plus, with reasoning
on, `REASONING_ALLOWANCE` for its level: providers don't always count
reasoning against `max_tokens`. `basis` counts the calls each covered. Retries are left out;
`lab run` says how many calls they could add.
"""

import dataclasses
from dataclasses import dataclass

from collusion_lab.backends import is_mock
from collusion_lab.config import expand
from collusion_lab.runner import Game, steps

CHARS_PER_TOKEN = 4
MIN_SEEN = 3  # cached replies needed before their mean stands in for the bound
# Reasoning tokens a call may bill beyond max_tokens, by level. Sized from our
# caches at max_tokens 600: Gemma 4 at low averaged 976 completion tokens a
# call (94% over 600), DeepSeek v4.1 Flash 1,490 and Grok 4.7 1,402.
REASONING_ALLOWANCE = {"low": 1500, "medium": 3000, "high": 6000}
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
    self_hosted: list[str]  # marked self_hosted: billed by GPU time, not here
    basis: dict  # calls estimated from observed means, and at max_tokens


def estimate(config, price_for, observed=None):
    """What `config` will cost; `observed` is `Cache.observed()`, if any."""
    calls = prompt = completion = 0
    cost = 0.0
    unpriced, self_hosted = [], []
    basis = {"observed": 0, "max_tokens": 0}
    for child in expand(config):
        seeds = len(child.seeds)
        for (agent, phase, bound), chars, turns in _paid_turns(child):
            tokens = chars // CHARS_PER_TOKEN
            mean, seen = (observed or {}).get(
                (agent.model, agent.reasoning, phase), (0, 0)
            )
            allowance = REASONING_ALLOWANCE.get(agent.reasoning, 0)
            reply = mean if seen >= MIN_SEEN else bound + allowance
            basis["observed" if seen >= MIN_SEEN else "max_tokens"] += turns * seeds
            calls += turns * seeds
            prompt += tokens * seeds
            completion += reply * turns * seeds
            if agent.self_hosted:
                self_hosted.append(agent.model)
                continue
            price = price_for(agent.model)
            if price is None:
                unpriced.append(agent.model)
            else:
                cost += seeds * (tokens * price[0] + reply * turns * price[1])
    unpriced = sorted(set(unpriced))
    cost = None if unpriced else cost
    hosted = sorted(set(self_hosted))
    return Estimate(calls, prompt, round(completion), cost, unpriced, hosted, basis)


def _paid_turns(config):
    """((agent, phase, max_tokens), prompt characters, turns) for each paid
    agent and phase over one game, max_tokens being that phase's limit: its
    turn slots in the order the game plays them (`runner.steps`), each phase a
    condition adds included (an audit perhaps answered by another model: then
    the agent is given that model) and the rounds an ending one cuts."""
    game = Game(config, config.seeds[0])
    m = game.market
    agents = {a.id: a for a in config.agents}
    counts = {}

    def count(agent, model, step, shown):
        number, phase = step.round, step.phase
        notices = game._notices(phase, number) if number else []
        messages = game._messages(phase, number, agent, shown, notices, step.added)
        answering = dataclasses.replace(agent, model=model)
        limit = (step.added and step.added[1].max_tokens) or agent.max_tokens
        slot = (agent.id, model, phase, limit)
        _, chars, turns = counts.get(slot, ((answering, phase, limit), 0, 0))
        chars += sum(len(x["content"]) for x in messages)
        counts[slot] = ((answering, phase, limit), chars, turns + 1)

    said = {}
    for step in steps(config, game.conditions):
        if step.phase == "talk":
            said = {a: TYPICAL_MESSAGE for a in game.agents}
        for agent_id in step.agents:
            agent = agents[agent_id]
            model = (step.added and step.added[1].model) or agent.model
            if not is_mock(model):
                count(agent, model, step, said if step.phase == m.move else {})
        if step.phase == m.move:
            prices = {a: m.joint_price for a in game.agents}
            game.history.append(
                {
                    "round": step.round,
                    "said": said,
                    "prices": prices,
                    "profits": m.profits(prices),
                }
            )
            said = {}
    return list(counts.values())
