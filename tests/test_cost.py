# Implements: backends/reported-cost, reproducibility/manifest
import json

import litellm

from collusion_lab.cache import Cache
from collusion_lab.runner import run_config

ROUTER = ["agents.0.model=openrouter/google/gemma-4-31b-it", "market.talk=false"]
PRICED = [
    {"content": '{"price": 7}', "cost": 0.0012},
    {"content": '{"price": 7}', "cost": 0.0008},
]


def read(run_dir, name):
    return [json.loads(line) for line in (run_dir / name).open()]


def manifest(run_dir):
    return json.loads((run_dir / "manifest.json").read_text())


def test_reported_cost_asked_for_and_logged(make_config, tmp_path, fake_model):
    fake_model.replies = list(PRICED)
    config = make_config(overrides=[*ROUTER, "market.rounds=2"])
    [run_dir] = run_config(config, tmp_path)
    assert fake_model.calls[0]["extra_body"]["usage"] == {"include": True}
    costs = [t["cost"] for t in read(run_dir, "timings.jsonl") if t["agent"] == "A"]
    assert costs == [0.0012, 0.0008]
    assert manifest(run_dir)["cost"] == 0.0012 + 0.0008
    assert manifest(run_dir)["unpriced_calls"] == 0


def test_reported_cost_asked_for_alongside_reasoning(make_config, tmp_path, fake_model):
    config = make_config(overrides=[*ROUTER, "agents.0.reasoning=low"])
    run_config(config, tmp_path)
    assert fake_model.calls[0]["extra_body"] == {
        "usage": {"include": True},
        "reasoning": {"effort": "low"},
    }


def test_reported_cost_wins_over_litellms_price(
    make_config, tmp_path, fake_model, monkeypatch
):
    monkeypatch.setattr(litellm, "completion_cost", lambda **kwargs: 99.0)
    fake_model.replies = list(PRICED)
    config = make_config(overrides=[*ROUTER, "market.rounds=2"])
    [run_dir] = run_config(config, tmp_path)
    assert manifest(run_dir)["cost"] == 0.0012 + 0.0008


def test_reported_cost_other_providers_keep_litellms_price(
    make_config, tmp_path, fake_model, monkeypatch
):
    monkeypatch.setattr(litellm, "completion_cost", lambda **kwargs: 0.5)
    config = make_config(
        overrides=["agents.0.model=openai/gpt-4.1-mini", "market.talk=false"]
    )
    [run_dir] = run_config(config, tmp_path)
    assert "extra_body" not in fake_model.calls[0]
    assert manifest(run_dir)["cost"] == 0.5 * 4


def test_reported_cost_unknown_stays_unknown(make_config, tmp_path, fake_model):
    fake_model.replies = [PRICED[0]]  # later replies report no cost
    [run_dir] = run_config(make_config(overrides=ROUTER), tmp_path)
    assert manifest(run_dir)["cost"] is None
    assert manifest(run_dir)["unpriced_calls"] == 3


def test_reported_cost_never_charged_twice_on_replay(make_config, tmp_path, fake_model):
    fake_model.replies = list(PRICED)
    config = make_config(overrides=[*ROUTER, "market.rounds=2"])
    cache = Cache(tmp_path / "cache.sqlite")
    run_config(config, tmp_path / "1", cache)
    [again] = run_config(config, tmp_path / "2", cache)
    assert manifest(again)["cost"] == 0
