# Implements: backends/serving-provider-logged, backends/pinned-route, reproducibility/replay-pinned
import json
import sqlite3

import pytest

from collusion_lab.cache import Cache
from collusion_lab.config import ConfigError
from collusion_lab.runner import run_config

MODEL = "openrouter/google/gemma-4-31b-it"
PAID = [f"agents.0.model={MODEL}", "market.talk=false", "market.rounds=2"]
SERVED = {
    "content": '{"price": 7}',
    "provider": "DeepInfra",
    "system_fingerprint": "fp-1",
}


def _lines(path):
    return [json.loads(line) for line in path.open()]


def test_serving_provider_logged_per_call_and_in_the_manifest(
    make_config, tmp_path, fake_model
):
    fake_model.replies = [SERVED, SERVED]
    [run] = run_config(make_config(overrides=PAID), tmp_path)
    timed = [t for t in _lines(run / "timings.jsonl") if t["agent"] == "A"]
    assert [(t["provider"], t["fingerprint"]) for t in timed] == [
        ("DeepInfra", "fp-1")
    ] * 2
    assert json.loads((run / "manifest.json").read_text())["providers"] == {
        "A": ["DeepInfra"]
    }


def test_serving_provider_kept_by_the_cache(make_config, tmp_path, fake_model):
    fake_model.replies = [SERVED, SERVED]
    config = make_config(overrides=PAID)
    run_config(config, tmp_path / "1", Cache(tmp_path / "c.sqlite"))
    [again] = run_config(config, tmp_path / "2", Cache(tmp_path / "c.sqlite"))
    timed = [t for t in _lines(again / "timings.jsonl") if t["agent"] == "A"]
    assert all(t["cached"] and t["provider"] == "DeepInfra" for t in timed)


def test_serving_provider_stays_out_of_the_turn_log(make_config, tmp_path, fake_model):
    fake_model.replies = [SERVED, SERVED]
    [run] = run_config(make_config(overrides=PAID), tmp_path)
    text = (run / "turns.jsonl").read_text()
    assert "DeepInfra" not in text and "fp-1" not in text


def test_pinned_route_asks_openrouter_for_one_host(make_config, tmp_path, fake_model):
    run_config(make_config(overrides=[*PAID, "agents.0.provider=DeepInfra"]), tmp_path)
    body = fake_model.calls[0]["extra_body"]
    assert body["provider"] == {"order": ["DeepInfra"], "allow_fallbacks": False}
    run_config(make_config(overrides=PAID), tmp_path / "free")
    assert "provider" not in fake_model.calls[-1]["extra_body"]


def test_pinned_route_joins_the_cache_key_only_when_set(
    make_config, tmp_path, fake_model
):
    def keys(overrides, name):
        cache = Cache(tmp_path / f"{name}.sqlite")
        run_config(make_config(overrides=overrides), tmp_path / name, cache)
        with sqlite3.connect(cache.path) as db:
            return {k for (k,) in db.execute("SELECT key FROM replies")}

    unset = keys(PAID, "unset")
    assert keys(PAID, "again") == unset
    assert keys([*PAID, "agents.0.provider=DeepInfra"], "pinned").isdisjoint(unset)
    config = make_config(overrides=PAID)
    assert all("provider" not in a for a in config.to_dict()["agents"])


def test_pinned_route_refused_off_openrouter(make_config):
    with pytest.raises(ConfigError, match="provider"):
        make_config(
            overrides=["agents.0.model=openai/gpt-4.1-mini", "agents.0.provider=x"]
        )
