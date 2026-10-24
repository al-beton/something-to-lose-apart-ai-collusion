# Implements: agents/mock-agents, backends/any-model, backends/sampling-from-config, backends/usage-logged
"""Backends turn a prompt into a reply: scripted mocks, or any model via LiteLLM.

A backend is anything with `async complete(messages, *, context, temperature,
max_tokens, seed) -> Reply`. Model backends read `messages`; mock backends
read `context` (the phase, the market and the history) and answer in the same
JSON a model would, so the whole reply path is exercised for free.

Mocks, by model name:
- `mock/nash`: always the Nash price;
- `mock/joint`: always the joint-profit price;
- `mock/tit-for-tat`: the joint-profit price, then the rivals' last mean price;
- `mock/random`: a uniform price from the grid, from the agent's seeded RNG;
- `mock/proposer`: names the joint-profit price and charges it, but one grid
  step below it every fifth round, so reports have proposals, agreements and
  defections to show;
- `mock/broken`: never valid JSON, for testing fallbacks.

Every other name goes to LiteLLM as it is (`openrouter/openai/gpt-4.1-mini`,
`anthropic/claude-haiku-5-5`, `ollama/llama3.2`, or `openai/<name>` with an
`api_base` for any OpenAI-compatible server). `drop_params` lets providers
without a `seed` parameter ignore it. LiteLLM is imported on first use, so
mock games never pay its import time.
"""

import json
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Reply:
    text: str
    usage: dict | None = None
    model_version: str | None = None
    seconds: float | None = None
    cost: float | None = None
    cached: bool = False


async def _acompletion(**kwargs):
    import litellm

    return await litellm.acompletion(**kwargs)


class LiteLLMBackend:
    def __init__(self, model, api_base=None):
        self.model = model
        self.api_base = api_base

    async def complete(self, messages, *, context, temperature, max_tokens, seed):
        extra = {"api_base": self.api_base} if self.api_base else {}
        started = time.perf_counter()
        response = await _acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            drop_params=True,
            **extra,
        )
        usage = getattr(response, "usage", None)
        return Reply(
            text=response.choices[0].message.content or "",
            usage=usage
            and {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
            },
            model_version=getattr(response, "model", None),
            seconds=time.perf_counter() - started,
            cost=_cost(response),
        )


def _cost(response):
    """LiteLLM's price for a response, or None when it can't price it."""
    try:
        import litellm

        return litellm.completion_cost(completion_response=response)
    # LiteLLM raises many error types for models it has no price for.
    except Exception:  # noqa: BLE001
        return None


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


def _proposer(context, rng):
    market = context["market"]
    price = market.on_grid(market.joint_price - 1)
    if context["round"] % 5:
        price = market.joint_price
    return price, f"Let's both charge {market.joint_price}."


def _random(context, rng):
    market = context["market"]
    return rng.randint(market.price_min, market.price_max), ""


_POLICIES = {
    "nash": _nash,
    "joint": _joint,
    "tit-for-tat": _tit_for_tat,
    "random": _random,
    "proposer": _proposer,
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


def is_mock(model):
    return model.startswith("mock/")


def backend_for(model, rng, api_base=None):
    """The backend a model name selects."""
    if not is_mock(model):
        return LiteLLMBackend(model, api_base)
    name = model.removeprefix("mock/")
    if name not in _POLICIES and name != "broken":
        known = ", ".join(f"mock/{p}" for p in [*_POLICIES, "broken"])
        raise ValueError(f"Unknown mock agent {model!r}; known: {known}.")
    return MockBackend(name, rng)
