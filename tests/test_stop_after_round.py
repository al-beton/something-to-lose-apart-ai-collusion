# Implements: market/stop-after-round
import json

import pytest
import yaml

from collusion_lab.cache import Cache
from collusion_lab.config import ConfigError
from collusion_lab.runner import run_config

MODEL = ["agents.0.model=openai/gpt-4.1-mini", "agents.1.model=openai/gpt-4.1-mini"]


def turns(run_dir):
    return [json.loads(line) for line in (run_dir / "turns.jsonl").open()]


def played(run_dir):
    keep = ("round", "phase", "agent", "messages", "reply", "used")
    return [{k: t[k] for k in keep} for t in turns(run_dir)]


def test_stop_after_round_matches_the_full_game_then_forks_from_the_cache(
    make_config, tmp_path, fake_model
):
    cache = Cache(tmp_path / "cache.sqlite")
    stopped = make_config(
        overrides=[*MODEL, "market.rounds=6", "market.stop_after_round=3"]
    )
    [base] = run_config(stopped, tmp_path / "base", cache)
    assert {t["round"] for t in turns(base)} == {1, 2, 3}
    first = turns(base)[0]["messages"]
    assert "6 rounds" in first[0]["content"]
    assert first[1]["content"].startswith("Round 1 of 6.")
    assert json.loads((base / "summary.json").read_text())["rounds"] == 3
    calls = len(fake_model.calls)

    full = make_config(overrides=[*MODEL, "market.rounds=6"])
    [forked] = run_config(full, tmp_path / "full", cache)
    # Rounds 1-3 came from the cache: only rounds 4-6 called the model.
    assert len(fake_model.calls) - calls == 3 * 2 * 2
    early = [t for t in played(forked) if t["round"] <= 3]
    assert early == played(base)


def test_stop_after_round_unset_plays_every_round_and_writes_as_before(
    make_config, tmp_path
):
    config = make_config()
    assert config.market.stop_after_round is None
    assert "stop_after_round" not in config.to_dict()["market"]
    [run_dir] = run_config(config, tmp_path / "runs")
    written = yaml.safe_load((run_dir / "config.yaml").read_text())
    assert "stop_after_round" not in written["market"]
    assert {t["round"] for t in turns(run_dir)} == {1, 2, 3, 4}

    stopped = make_config(overrides=["market.stop_after_round=2"])
    assert stopped.to_dict()["market"]["stop_after_round"] == 2


@pytest.mark.parametrize("value", [0, 5, "three", True])
def test_stop_after_round_must_be_a_round_of_the_game(make_config, value):
    with pytest.raises(ConfigError, match="stop_after_round"):
        make_config(overrides=[f"market.stop_after_round={value}"])
