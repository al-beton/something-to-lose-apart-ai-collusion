# Implements: agents/mock-agents
"""Backends turn a prompt into a reply. Mock backends are scripted policies.

A backend is anything with `async complete(messages, *, context, temperature,
max_tokens, seed) -> Reply`. Model backends read `messages`; mock backends
read `context` (the phase, the market and the history) and answer in the same
JSON a model would, so the whole reply path is exercised for free.

Mocks, by model name:
- `mock/nash`: always the Nash price;
- `mock/joint`: always the joint-profit price;
- `mock/tit-for-tat`: the joint-profit price, then the rivals' last mean price;
- `mock/random`: a uniform price from the grid, from the agent's seeded RNG;
- `mock/broken`: never valid JSON, for testing fallbacks.
"""

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Reply:
    text: str


def _nash(context, rng):
    return context["market"].nash_price, "I will price at the market level."


def _joint(context, rng):
    return context["market"].joint_price, "I will keep prices high."


def _tit_for_tat(context, rng):
    history = context["history"]
    if not history:
        return context["market"].joint_price, "I will match your last price."
    rivals = [p for f, p in history[-1]["prices"].items() if f != context["me"]]
    mean_rival = sum(rivals) / len(rivals)
    return context["market"].on_grid(mean_rival), "I will match your last price."


def _random(context, rng):
    market = context["market"]
    return rng.randint(market.price_min, market.price_max), ""


_POLICIES = {
    "nash": _nash,
    "joint": _joint,
    "tit-for-tat": _tit_for_tat,
    "random": _random,
}


class MockBackend:
    def __init__(self, policy, rng):
        self.policy = policy
        self.rng = rng

    async def complete(self, messages, *, context, temperature, max_tokens, seed):
        if self.policy == "broken":
            return Reply("I'd rather not say.")
        price, message = _POLICIES[self.policy](context, self.rng)
        if context["phase"] == "talk":
            return Reply(json.dumps({"message": message}))
        return Reply(json.dumps({"price": price}))


def backend_for(model, rng):
    """The backend a model name selects."""
    provider, _, name = model.partition("/")
    if provider == "mock":
        if name not in _POLICIES and name != "broken":
            known = ", ".join(f"mock/{p}" for p in [*_POLICIES, "broken"])
            raise ValueError(f"Unknown mock agent {model!r}; known: {known}.")
        return MockBackend(name, rng)
    raise ValueError(f"No backend for {model!r} yet; only mock/ agents run.")
