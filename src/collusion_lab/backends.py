# Implements: agents/mock-agents, backends/any-model, backends/sampling-from-config, backends/usage-logged, backends/transient-errors-retried, backends/shared-rate-limit, backends/reported-cost, backends/spend-cap, backends/reasoning-setting, logs/reasoning-logged, agents/json-mode, agents/unreadable-explained, backends/quiet-provider-logs, backends/self-hosted, backends/keys-from-environment
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
- `mock/broken`: never valid JSON, for testing fallbacks;
- `mock/solicitor?...`: a partner that proposes collusion first, with its
  settings in the name (`partners.py`).
All but `mock/broken` deny coordinating when audited, and spend free time
with one fixed line, which never draws from their seeded rng.

Every other name goes to LiteLLM as it is (`openrouter/openai/gpt-4.1-mini`,
`anthropic/claude-haiku-5-5`, `ollama/llama3.2`, or `openai/<name>` with an
`api_base` for any OpenAI-compatible server, such as an open model on Modal:
see `deploy/modal_vllm.py`). A model at its own address gets only the key in
the variable `api_key_env` names (a placeholder when none is named, so no
provider's own key goes there). One its agent marks `self_hosted` is billed by
its host's GPU time, so LiteLLM's per-token price is never applied to it and
a host still starting up is waited for; any other address is priced as usual.
`drop_params` lets providers without a `seed` parameter ignore it. LiteLLM is imported on first use, so
mock games never pay its import time.

`json_mode` asks for `response_format: {"type": "json_object"}`, which
`drop_params` drops for providers that can't do it. Each reply keeps the
provider's finish reason (`length` means it hit the token limit).

Cost: OpenRouter calls ask for usage accounting (`usage: {include: true}`)
and record the `usage.cost` OpenRouter reports, which LiteLLM's price table
can't give for OpenRouter model names. Every other call keeps LiteLLM's price,
or None when it has none.

Spend: every model backend in a run shares one `Budget`. Right before each
request (after any rate-limit wait or retry delay) it checks that the run's
fresh calls haven't cost more than its cap, and raises `ModelCallError` if
they have; each answered call adds its cost. A call with no known cost adds
nothing.

An agent's `reasoning` (off, low, medium, high) goes to OpenRouter as its
`reasoning` request field (`{"effort": ...}`, or `{"enabled": false}` for
off) and to every other provider as LiteLLM's `reasoning_effort` (`none` for
off), which `drop_params` drops for models that don't take it. The reasoning
text a provider returns (`reasoning_content` or `reasoning`) and its
reasoning-token count come back on the Reply.

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
import logging
import os
import re
import time
from dataclasses import dataclass

from collusion_lab.partners import Solicitor

RETRIES = 5
FIRST_WAIT = 2
TIMEOUT = 180  # seconds before a hung call is cut off and retried
MAX_WAIT = 120  # a rate limit lifting later than this stops the run
# A self-hosted model's host answers 503 while it starts (Modal loads the
# weights for minutes); calls keep trying that long, as deploy/modal_vllm.py
# allows its container to start.
COLD_START = 20 * 60
COLD_WAIT = 15
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
    reasoning: str | None = None
    finish_reason: str | None = None


def quiet_litellm(litellm):
    """Turn off LiteLLM's info and debug output ("LiteLLM.Info: …", its
    feedback banner on every error) unless LITELLM_LOG asks for it."""
    if os.environ.get("LITELLM_LOG"):
        return
    litellm.suppress_debug_info = True
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)


async def _acompletion(**kwargs):
    import litellm

    quiet_litellm(litellm)
    return await litellm.acompletion(**kwargs)


class Budget:
    """What a run's calls have cost, against an optional cap in dollars, and
    how many fresh calls have been answered so far (for live progress)."""

    def __init__(self, cap=None):
        self.cap = cap
        self.spent = 0.0
        self.calls = 0

    def check(self, model):
        if self.cap is not None and self.spent > self.cap:
            raise ModelCallError(
                f"{model}: spend cap of ${self.cap:g} passed (${self.spent:.4f} spent)"
            )


class RateGates:
    """When each model may be called again, shared by every game in a run."""

    def __init__(self):
        self.until = {}

    async def wait(self, model):
        # Another game may push the time later while this one sleeps.
        while (delay := self.until.get(model, 0) - _now()) > 0:
            await _sleep(delay)

    def hold(self, model, until):
        self.until[model] = max(until, self.until.get(model, 0))


def _one_line(error, secrets=()):
    """The error on one line, with any key it echoes masked."""
    text = str(error)
    for secret in secrets:
        text = text.replace(secret, "***")
    text = " ".join(text.split())
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
    def __init__(self, model, api_base=None, gates=None, budget=None, **options):
        """`options` are the agent's request settings: `reasoning` and
        `json_mode`."""
        self.model = model
        self.api_base = api_base
        self.gates = gates or RateGates()
        self.budget = budget or Budget()
        self.reasoning = options.get("reasoning")
        self.json_mode = options.get("json_mode", False)
        self.api_key_env = options.get("api_key_env")
        self.self_hosted = options.get("self_hosted", False)

    def _extra(self):
        """Request fields beyond the sampling ones: address, usage, reasoning
        and JSON mode."""
        extra = {}
        if self.api_base:
            extra = {"api_base": self.api_base, "api_key": self._address_key()}
        if self.json_mode:
            extra["response_format"] = {"type": "json_object"}
        off = self.reasoning == "off"
        if self.model.startswith("openrouter/"):
            body = {"usage": {"include": True}}
            if self.reasoning is not None:
                body["reasoning"] = (
                    {"enabled": False} if off else {"effort": self.reasoning}
                )
            extra["extra_body"] = body
        elif self.reasoning is not None:
            extra["reasoning_effort"] = "none" if off else self.reasoning
        return extra

    def _starting(self, error, started):
        """Whether a self-hosted model's host is still starting up."""
        starting = getattr(error, "status_code", None) == 503
        return self.self_hosted and starting and _now() - started < COLD_START

    def _secrets(self, request):
        """Keys an error might echo: the one sent, and any in the environment."""
        keys = [request.get("api_key")]
        keys += [v for k, v in os.environ.items() if k.endswith("_API_KEY")]
        if self.api_key_env:
            keys.append(os.environ.get(self.api_key_env))
        return [k for k in keys if k and len(k) >= 8]

    def _address_key(self):
        """The key for a model at its own address, from `api_key_env` only."""
        if not self.api_key_env:
            return "none"
        if key := os.environ.get(self.api_key_env):
            return key
        raise ModelCallError(
            f"{self.model}: {self.api_key_env} isn't set in the environment or .env"
        )

    async def complete(self, messages, *, context, temperature, max_tokens, seed):
        extra = self._extra()
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
        cost = None if self.self_hosted else _cost(response)  # self-hosted: GPU time
        self.budget.spent += cost or 0
        self.budget.calls += 1
        message = response.choices[0].message
        return Reply(
            text=message.content or "",
            usage=usage and _usage(usage),
            reasoning=getattr(message, "reasoning_content", None)
            or getattr(message, "reasoning", None),
            finish_reason=getattr(response.choices[0], "finish_reason", None),
            model_version=getattr(response, "model", None),
            seconds=time.perf_counter() - started,
            cost=cost,
            retries=retries or None,
        )

    async def _call(self, **request):
        """The response, and the errors retried on the way to it."""
        retries = []
        tries = 0  # retries other than waiting for a host to start
        wait = FIRST_WAIT
        started = _now()
        while True:
            await self.gates.wait(self.model)
            self.budget.check(self.model)
            try:
                return await _acompletion(**request), retries
            except Exception as error:
                if not _provider_error(error):
                    raise
                said = _one_line(error, self._secrets(request))
                if self._starting(error, started):
                    retries.append({"error": said})
                    await _sleep(COLD_WAIT)
                    continue
                if not _transient(error):
                    raise ModelCallError(f"{self.model}: {said}") from None
                if tries == RETRIES:
                    raise ModelCallError(
                        f"{self.model}: gave up after {RETRIES + 1} tries: {said}"
                    ) from None
                retries.append({"error": said})
                tries += 1
                if (until := reset_time(error)) and until > _now():
                    if until - _now() > MAX_WAIT:
                        lifts = time.strftime(
                            "%Y-%m-%d %H:%M %Z", time.localtime(until)
                        )
                        raise ModelCallError(
                            f"{self.model}: rate-limited; the limit lifts at {lifts}"
                        ) from error
                    self.gates.hold(self.model, until)
                else:
                    await _sleep(wait)
                    wait *= 2


def _usage(usage):
    counted = {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
    }
    details = getattr(usage, "completion_tokens_details", None)
    if (thought := getattr(details, "reasoning_tokens", None)) is not None:
        counted["reasoning_tokens"] = thought
    return counted


def _cost(response):
    """What the provider says the call cost, else LiteLLM's price for it, or
    None when neither is known."""
    reported = getattr(getattr(response, "usage", None), "cost", None)
    if isinstance(reported, int | float):
        return reported
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
        if context["phase"] == "audit":
            answer = "We set our prices independently."
            return Reply(json.dumps({"answer": answer, "admits": False}))
        if context["phase"] == "leisure":
            return Reply(LEISURE_REPLY)  # before any policy, so the rng is untouched
        price, message = _POLICIES[self.policy](context, self.rng)
        if context["phase"] == "talk":
            return Reply(json.dumps({"message": message}))
        return Reply(json.dumps({"price": price}))


LEISURE_REPLY = "I took a walk and thought about nothing much."


def is_mock(model):
    return model.startswith("mock/")


def backend_for(model, rng, api_base=None, gates=None, **options):
    """The backend a model name selects; `options` (budget, reasoning, json_mode,
    api_key_env) go to model backends."""
    if not is_mock(model):
        return LiteLLMBackend(model, api_base, gates, **options)
    name = model.removeprefix("mock/")
    if name.split("?")[0] == "solicitor":
        return Solicitor(model)
    if name not in _POLICIES and name != "broken":
        known = ", ".join(f"mock/{p}" for p in [*_POLICIES, "broken", "solicitor"])
        raise ValueError(f"Unknown mock agent {model!r}; known: {known}.")
    return MockBackend(name, rng)
