# Implements: backends/spend-asks-first
"""What a model costs per token, for estimating a run before it spends.

`price_for(model)` gives (dollars per prompt token, dollars per completion
token), or None when no price is known. Mock agents are free. OpenRouter
models are priced from OpenRouter's public model list, fetched once per
process (no key needed); every other model from LiteLLM's price table.
"""

import functools
import json
import urllib.request

from collusion_lab.backends import is_mock

OPENROUTER_MODELS = "https://openrouter.ai/api/v1/models"


@functools.cache
def _openrouter_prices():
    """OpenRouter's prices by model id, or {} when the list can't be read."""
    try:
        with urllib.request.urlopen(OPENROUTER_MODELS, timeout=10) as response:
            models = json.load(response)["data"]
        return {
            m["id"]: (float(m["pricing"]["prompt"]), float(m["pricing"]["completion"]))
            for m in models
            if "pricing" in m
        }
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def price_for(model):
    if is_mock(model):
        return (0.0, 0.0)
    if model.startswith("openrouter/"):
        return _openrouter_prices().get(model.removeprefix("openrouter/"))
    import litellm

    entry = litellm.model_cost.get(model) or litellm.model_cost.get(
        model.split("/", 1)[-1]
    )
    if entry and "input_cost_per_token" in entry:
        return (entry["input_cost_per_token"], entry.get("output_cost_per_token", 0))
    return None
