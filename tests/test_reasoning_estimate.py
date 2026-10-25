# Implements: backends/reasoning-in-estimate
import json
import sqlite3

import pytest

from collusion_lab import cli
from collusion_lab.cache import Cache
from collusion_lab.estimate import REASONING_ALLOWANCE, estimate
from collusion_lab.runner import run_config

MODEL = "openrouter/example/reasoner"
PER_TOKEN = (1e-6, 4e-6)  # dollars per prompt token, per completion token
PAID = [f"agents.0.model={MODEL}", "agents.0.reasoning=low", "agents.0.max_tokens=500"]


def price_for(model):
    return PER_TOKEN


def test_reasoning_in_estimate_bounds_unseen_calls_by_max_tokens_and_an_allowance(
    make_config,
):
    guess = estimate(make_config(overrides=PAID), price_for)  # reasoning low
    assert guess.completion_tokens == guess.calls * (500 + REASONING_ALLOWANCE["low"])
    assert guess.basis == {"observed": 0, "max_tokens": guess.calls}
    off = estimate(make_config(overrides=[*PAID, "agents.0.reasoning=off"]), price_for)
    assert off.completion_tokens == off.calls * 500
    levels = [
        estimate(make_config(overrides=[*PAID, f"agents.0.reasoning={x}"]), price_for)
        for x in ("low", "medium", "high")
    ]
    assert [g.cost for g in levels] == sorted(g.cost for g in levels)


def test_reasoning_in_estimate_uses_the_caches_observed_means(
    make_config, tmp_path, fake_model
):
    config = make_config(overrides=PAID)  # 4 rounds, talking
    cache = Cache(tmp_path / "c.sqlite")
    run_config(config, tmp_path / "runs", cache)
    seen = cache.observed()  # the fake bills 3 completion tokens a call
    assert seen[(MODEL, "low", "talk")] == (3, 4)
    assert seen[(MODEL, "low", "price")] == (3, 4)
    guess = estimate(config, price_for, seen)
    assert guess.basis == {"observed": 8, "max_tokens": 0}
    assert guess.completion_tokens == 8 * 3
    # Another reasoning setting hasn't been seen: back to the bound.
    medium = make_config(overrides=[*PAID, "agents.0.reasoning=medium"])
    assert estimate(medium, price_for, seen).basis == {"observed": 0, "max_tokens": 8}


def test_reasoning_in_estimate_matches_a_cached_runs_known_cost(
    make_config, tmp_path, fake_model
):
    overrides = [*PAID, "market.talk=false", "seeds=[0, 1, 2]"]
    config = make_config(overrides=overrides)
    cache = Cache(tmp_path / "c.sqlite")
    dirs = run_config(config, tmp_path / "runs", cache)
    billed = sum(
        json.loads((d / "manifest.json").read_text())["tokens"]["completion"]
        for d in dirs
    )
    out_only = lambda model: (0.0, PER_TOKEN[1])
    guess = estimate(config, out_only, cache.observed())
    assert guess.completion_tokens == billed
    assert guess.cost == pytest.approx(billed * PER_TOKEN[1])


def test_reasoning_in_estimate_says_which_basis(tmp_path, capsys, monkeypatch):
    config = tmp_path / "paid.yaml"
    config.write_text(
        "name: paid\nseeds: [0]\nmarket: {rounds: 2, talk: false}\nagents:\n"
        f"  - {{id: A, model: {MODEL}, max_tokens: 500}}\n  - {{id: B, model: mock/nash}}\n"
    )
    monkeypatch.setattr("collusion_lab.cli.price_for", price_for)
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    cache = str(tmp_path / "c.sqlite")
    assert cli.main(["run", str(config), "--cache-path", cache]) == 1
    out = capsys.readouterr().out
    assert "completion tokens: max_tokens, plus a reasoning allowance" in out
    assert "for 2 calls" in out


def test_reasoning_in_estimate_cache_records_leave_replay_alone(
    make_config, tmp_path, fake_model
):
    config = make_config(overrides=[*PAID, "market.talk=false"])
    cache = Cache(tmp_path / "c.sqlite")
    [first] = run_config(config, tmp_path / "1", cache)
    with sqlite3.connect(cache.path) as db:
        stored = [json.loads(r) for (r,) in db.execute("SELECT reply FROM replies")]
    assert all(
        r["about"] == {"model": MODEL, "reasoning": "low", "phase": "price"}
        for r in stored
    )
    calls = len(fake_model.calls)
    [again] = run_config(config, tmp_path / "2", Cache(tmp_path / "c.sqlite"))
    assert len(fake_model.calls) == calls
    assert (first / "turns.jsonl").read_bytes() == (again / "turns.jsonl").read_bytes()
