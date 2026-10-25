# Implements: market/scenarios, market/logit, market/known-benchmarks, reproducibility/replay-pinned
import hashlib
import json
import sqlite3
from pathlib import Path
from statistics import mean

import pytest
import yaml

from collusion_lab.cache import Cache
from collusion_lab.config import ConfigError
from collusion_lab.market import Bertrand, Logit, market_for
from collusion_lab.runner import run_config

RUNS = Path(__file__).parent.parent / "runs"

# Every condition at once, on a short game, one model firm and one script.
EVERYTHING = """
name: pinned
seeds: [3]
market:
  rounds: 6
  history_window: 2
summary:
  last_rounds: 2
agents:
  - {id: A, model: openrouter/openai/gpt-4.1-mini}
  - {id: B, model: mock/proposer}
conditions:
  instruction: {enabled: true}
  outage: {enabled: true, start: 2, end: 3}
  free_time: {enabled: true, allowance: 3}
  audit: {enabled: true, round: 4, end: false}
"""

# What the run above wrote before markets became swappable. A change that
# moves any of them changes what replays, or what the cache answers.
PINNED_TURNS = "8e51c8e68b1b5fe00fcbf2805e32883c7a7d847544d5c0de68b016706fc6b84a"
PINNED_CONFIG = "36a4482a17de3bc9e88d1ae01c4506ee99014c6fde3c4d753550a9ac1dfd97b2"
PINNED_KEYS = "c5cd32b45651ef80ada1debc1a4128c63b2513faf5049838a92d29535c75b354"


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _play(make_config, tmp_path, overrides=()):
    cache = Cache(tmp_path / "cache.sqlite")
    [run] = run_config(make_config(EVERYTHING, overrides), tmp_path / "out", cache)
    return run, cache


def test_replay_pinned_turn_log_config_and_cache_keys(
    make_config, tmp_path, fake_model
):
    run, cache = _play(make_config, tmp_path)
    with sqlite3.connect(cache.path) as db:
        keys = sorted(k for (k,) in db.execute("SELECT key FROM replies"))
    assert _sha((run / "turns.jsonl").read_bytes()) == PINNED_TURNS
    assert _sha((run / "config.yaml").read_bytes()) == PINNED_CONFIG
    assert _sha("\n".join(keys).encode()) == PINNED_KEYS


def _committed_runs():
    return sorted(p.parent for p in RUNS.glob("**/turns.compact.jsonl"))


def test_replay_pinned_committed_runs_keep_their_gains():
    """Every committed run's gains, recomputed from the prices it logged in the
    market its config names, match the summary it wrote."""
    runs = _committed_runs()
    assert runs
    for run in runs:
        config = yaml.safe_load((run / "config.yaml").read_text())
        summary = json.loads((run / "summary.json").read_text())
        market = market_for(config["market"], len(config["agents"]))
        rounds = {}
        for line in (run / "turns.compact.jsonl").read_text().splitlines():
            turn = json.loads(line)
            if turn["phase"] == "price":
                rounds.setdefault(turn["round"], {})[turn["agent"]] = turn["used"][
                    "price"
                ]
        last = [rounds[n] for n in sorted(rounds)][-summary["last_rounds"] :]
        profits = [market.profits(prices) for prices in last]
        for firm, gain in summary["gain"].items():
            expected = market.gain(mean(p[firm] for p in profits))
            assert expected == pytest.approx(gain), (run, firm)


def test_scenarios_default_to_bertrand_from_the_config(make_config):
    config = make_config()
    assert market_for(config.market, 2) == Bertrand()
    assert "kind" not in config.to_dict()["market"]
    assert "params" not in config.to_dict()["market"]


def test_scenarios_pick_the_market_by_kind(make_config):
    grid = ["market.price_min=10", "market.price_max=25"]
    config = make_config(overrides=["market.kind=logit", *grid])
    market = market_for(config.market, 2)
    assert isinstance(market, Logit)
    assert config.to_dict()["market"]["kind"] == "logit"


def test_scenarios_refuse_an_unknown_kind_or_parameter(make_config):
    with pytest.raises(ConfigError, match="market.kind"):
        make_config(overrides=["market.kind=hotelling"])
    with pytest.raises(ConfigError, match="market"):
        make_config(overrides=["market.kind=logit", "market.params={sigma: 1}"])


def test_scenarios_supply_their_prompt_values():
    assert Bertrand().prompt_values() == {"price_min": 1, "price_max": 12}
    assert Logit().prompt_values() == {"price_min": 10, "price_max": 25, "cost": 10}


def test_logit_benchmarks_put_nash_at_14_and_joint_profit_at_19():
    market = Logit()
    assert (market.nash_price, market.joint_price) == (14, 19)
    assert (Logit(firms=3).nash_price, Logit(firms=3).joint_price) == (14, 20)


def test_logit_shares_demand_with_an_outside_good():
    market = Logit()
    sold = market.quantities({"A": 15, "B": 15})
    assert sold["A"] == pytest.approx(100 * 7.389056 / (2 * 7.389056 + 1), rel=1e-6)
    cheaper = market.quantities({"A": 14, "B": 16})
    assert cheaper["A"] > sold["A"] > cheaper["B"]
    profits = market.profits({"A": 15, "B": 15})
    assert profits["A"] == pytest.approx(5 * sold["A"])


@pytest.mark.parametrize("kind", ["bertrand", "logit"])
def test_scenarios_play_every_condition_unchanged(make_config, tmp_path, kind):
    overrides = [
        f"market.kind={kind}",
        "agents.0.model=mock/tit-for-tat",
        *(["market.price_min=10", "market.price_max=25"] if kind == "logit" else []),
    ]
    run, _ = _play(make_config, tmp_path, overrides)
    summary = json.loads((run / "summary.json").read_text())
    market = market_for(make_config(EVERYTHING, overrides).market, 2)
    turns = [json.loads(line) for line in (run / "turns.jsonl").open()]
    assert {t["phase"] for t in turns} == {"talk", "price", "audit", "leisure"}
    assert {"audit", "free_time"} <= summary.keys()
    prices = [t["used"]["price"] for t in turns if t["phase"] == "price"]
    assert all(market.price_min <= p <= market.price_max for p in prices)
    first = next(t for t in turns if t["phase"] == "price")
    assert (
        f"from {market.price_min} to {market.price_max}"
        in (first["messages"][-1]["content"])
    )


def test_scenarios_report_and_chart_each_runs_own_market(make_config, tmp_path):
    from collusion_lab import charts
    from collusion_lab.report.games import load_game
    from collusion_lab.report.page import build_report

    logit = ["market.kind=logit", "market.price_min=10", "market.price_max=25"]
    [run] = run_config(make_config(overrides=logit), tmp_path / "out")
    assert charts.market(run) == Logit()
    assert load_game(run).market == Logit()
    assert "Nash price 14, joint-profit price 19" in build_report(tmp_path / "out")
