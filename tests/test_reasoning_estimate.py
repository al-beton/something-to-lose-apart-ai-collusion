# Implements: backends/reasoning-in-estimate
import pytest

from collusion_lab.estimate import REASONING_TOKENS, REPLY_TOKENS, estimate

MODEL = "openrouter/example/reasoner"
PER_TOKEN = (1e-6, 4e-6)  # dollars per prompt token, per completion token


def price_for(model):
    return PER_TOKEN


def guess(make_config, *overrides):
    paid = [f"agents.0.model={MODEL}", *overrides]
    return estimate(make_config(overrides=paid), price_for)


@pytest.mark.parametrize("level", ["low", "medium", "high"])
def test_reasoning_in_estimate_adds_tokens_per_call(make_config, level):
    base = guess(make_config)
    on = guess(make_config, f"agents.0.reasoning={level}")
    extra = base.calls * REASONING_TOKENS[level]
    assert on.calls == base.calls
    assert on.prompt_tokens == base.prompt_tokens
    assert on.completion_tokens == base.completion_tokens + extra
    assert on.cost == pytest.approx(base.cost + extra * PER_TOKEN[1])


def test_reasoning_in_estimate_rises_with_the_level(make_config):
    costs = [
        guess(make_config, f"agents.0.reasoning={x}").cost for x in REASONING_TOKENS
    ]
    assert costs == sorted(costs) and len(set(costs)) == 3


def test_reasoning_in_estimate_off_or_unset_is_unchanged(make_config):
    unset = guess(make_config)
    off = guess(make_config, "agents.0.reasoning=off")
    assert off == unset
    assert unset.completion_tokens == unset.calls * REPLY_TOKENS
