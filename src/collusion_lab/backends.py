# Implements: agents/mock-agents, backends/any-model, backends/sampling-from-config, backends/usage-logged, backends/transient-errors-retried, backends/shared-rate-limit
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
- `mock/broken`: never valid JSON, for testing fallbacks.

Every other name goes to LiteLLM as it is (`openrouter/openai/gpt-4.1-mini`,
`anthropic/claude-haiku-5-5`, `ollama/llama3.2`, or `openai/<name>` with an
`api_base` for any OpenAI-compatible server). `drop_params` lets providers
without a `seed` parameter ignore it. LiteLLM is imported on first use, so
mock games never pay its import time.

Provider errors: rate limits, timeouts and server errors are retried with
doubling waits (`RETRIES` times); anything else (a bad key, an unknown model)
raises `ModelCallError` at once. Exceptions that aren't from a provider
(no status code, not a timeout) pass through untouched. When a rate limit says when it lifts (the
`X-RateLimit-Reset` or `Retry-After` header, or OpenRouter's copy of its
headers inside the error body), the model's entry in the shared `RateGates`
holds every call to that model, from any game, until then. Each error got
past is listed in the reply's `retries`, which goes to the timings log.
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass

RETRIES = 5
FIRST_WAIT = 2
TIMEOUT = 180  # seconds before a hung call is cut off and retried
MAX_WAIT = 120  # a rate limit lifting later than this stops the run
TRANSIENT = {408, 409, 425, 429}  # plus every 5xx
RESET_IN_BODY = re.compile(r"X-RateLimit-Reset\W+(\d+)", re.IGNORECASE)

# Patched in tests, so retries never really sleep.
_sleep = asyncio.sleep
_now = time.time


class ModelCallError(Exception):
    """A model call that failed for good, in one line naming the model."""


@dataclass(frozen=True)
class Reply:
    text: str
    usage: dict | None = None
    model_version: str | None = None
    seconds: float | None = None
    cost: float | None = None
    cached: bool = False
    retries: list | None = None


async def _acompletion(**kwargs):
    import litellm

    return await litellm.acompletion(**kwargs)


class RateGates:
    """When each model may be called again, shared by every game in a run."""

    def __init__(self):
        self.until = {}

    async def wait(self, model):
        delay = self.until.get(model, 0) - _now()
        if delay > 0:
            await _sleep(delay)

    def hold(self, model, until):
        self.until[model] = max(until, self.until.get(model, 0))


def _one_line(error):
    text = " ".join(str(error).split())
    return f"{type(error).__name__}: {text[:200]}"


def _provider_error(error):
    """Whether a provider (not our own code) raised this."""
    status = getattr(error, "status_code", None)
    return isinstance(status, int) or isinstance(error, TimeoutError | ConnectionError)


def _transient(error):
    status = getattr(error, "status_code", None)
    if isinstance(status, int):
        return status in TRANSIENT or status >= 500
    return True  # a timeout or a dropped connection


def reset_time(error):
    """When a rate limit lifts (seconds since the epoch), or None if unsaid."""
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None) or {}
    value = headers.get("x-ratelimit-reset")
    if value is None and (found := RESET_IN_BODY.search(str(error))):
        value = found.group(1)
    if value is None and (after := headers.get("retry-after")):
        value = after
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number > 1e12:  # milliseconds since the epoch, as OpenRouter sends it
        return number / 1000
    if number > 1e9:  # seconds since the epoch
        return number
    return _now() + number  # seconds from now


class LiteLLMBackend:
    def __init__(self, model, api_base=None, gates=None):
        self.model = model
        self.api_base = api_base
        self.gates = gates or RateGates()

    async def complete(self, messages, *, context, temperature, max_tokens, seed):
        extra = {"api_base": self.api_base} if self.api_base else {}
        started = time.perf_counter()
        response, retries = await self._call(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            drop_params=True,
            timeout=TIMEOUT,
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
            retries=retries or None,
        )

    async def _call(self, **request):
        """The response, and the errors retried on the way to it."""
        retries = []
        wait = FIRST_WAIT
        while True:
            await self.gates.wait(self.model)
            try:
                return await _acompletion(**request), retries
            except Exception as error:
                if not _provider_error(error):
                    raise
                if not _transient(error):
                    raise ModelCallError(f"{self.model}: {_one_line(error)}") from error
                if len(retries) == RETRIES:
                    raise ModelCallError(
                        f"{self.model}: gave up after {RETRIES + 1} tries: "
                        f"{_one_line(error)}"
                    ) from error
                retries.append({"error": _one_line(error)})
                if (until := reset_time(error)) and until > _now():
                    if until - _now() > MAX_WAIT:
                        lifts = time.strftime("%H:%M:%S", time.localtime(until))
                        raise ModelCallError(
                            f"{self.model}: rate-limited; the limit lifts at {lifts}"
                        ) from error
                    self.gates.hold(self.model, until)
                else:
                    await _sleep(wait)
                    wait *= 2


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


def is_mock(model):
    return model.startswith("mock/")


def backend_for(model, rng, api_base=None, gates=None):
    """The backend a model name selects."""
    if not is_mock(model):
        return LiteLLMBackend(model, api_base, gates)
    name = model.removeprefix("mock/")
    if name not in _POLICIES and name != "broken":
        known = ", ".join(f"mock/{p}" for p in [*_POLICIES, "broken"])
        raise ValueError(f"Unknown mock agent {model!r}; known: {known}.")
    return MockBackend(name, rng)
