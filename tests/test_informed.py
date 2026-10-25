# Implements: market/show-payoffs, market/history-window
import json

import pytest

from collusion_lab.config import ConfigError, load_config
from collusion_lab.estimate import estimate
from collusion_lab.market import Bertrand, Cournot, Logit
from collusion_lab.prices import price_for
from collusion_lab.runner import run_config

SHOW = ["market.show_payoffs=true"]
E5_MARKET = Bertrand(c=1.0, price_max=11)  # the midpoint-at-Nash market


def _turns(run):
    return [json.loads(line) for line in (run / "turns.jsonl").open()]


@pytest.mark.parametrize("market", [E5_MARKET, Logit(), Cournot()])
def test_show_payoffs_table_matches_the_markets_profits(market):
    rows = market.payoff_rows(2)
    assert [own for own, _ in rows] == list(market.grid)
    for own, cells in rows:
        assert len(cells) == len(market.grid)
        for rival, profit in zip(market.grid, cells, strict=True):
            assert profit == market.profits({"A": own, "B": rival})["A"]
    assert len(rows) == 11 or market is not E5_MARKET


def test_show_payoffs_in_every_system_prompt_unmarked(make_config, tmp_path):
    overrides = [*SHOW, "market.c=1.0", "market.price_max=11"]
    [run] = run_config(make_config(overrides=overrides), tmp_path)
    systems = {t["messages"][0]["content"] for t in _turns(run)}
    assert len(systems) == 2  # one per firm, the same every turn
    for system in systems:
        assert (
            "This table gives your profit for each pair of prices. Rows: your "
            "price. Columns: your rival's price." in system
        )
        assert "| 6 | 42 | 48 |" in system  # row 6: your price 6, rival at 1, 2
        assert "nash" not in system.lower() and "joint" not in system.lower()


def test_show_payoffs_says_what_columns_mean_with_more_firms(make_config, tmp_path):
    three = ["agents.2={id: C, model: mock/nash}", *SHOW]
    [run] = run_config(make_config(overrides=three), tmp_path)
    system = _turns(run)[0]["messages"][0]["content"]
    assert "Columns: the price each of your rivals charges." in system
    cournot = [*SHOW, "market.kind=cournot", "market.price_max=15"]
    [run] = run_config(make_config(overrides=cournot), tmp_path / "cournot")
    system = _turns(run)[0]["messages"][0]["content"]
    assert "each pair of quantities. Rows: your quantity." in system


def test_show_payoffs_off_by_default_leaves_configs_as_they_were(make_config):
    config = make_config()
    assert config.market.show_payoffs is False
    assert "show_payoffs" not in config.to_dict()["market"]
    assert make_config(overrides=SHOW).to_dict()["market"]["show_payoffs"] is True


def test_show_payoffs_refused_for_bid_rigging(make_config):
    bid = [*SHOW, "market.kind=bid", "market.price_min=10", "market.price_max=30"]
    with pytest.raises(ConfigError, match="show_payoffs"):
        make_config(overrides=bid)


def test_show_payoffs_counted_in_the_cost_estimate(make_config):
    paid = ["agents.0.model=openrouter/openai/gpt-4.1-mini"]
    plain = estimate(make_config(overrides=paid), price_for)
    shown = estimate(make_config(overrides=[*paid, *SHOW]), price_for)
    assert shown.prompt_tokens > plain.prompt_tokens + 100


def test_history_window_full_shows_every_round_in_full(make_config, tmp_path):
    overrides = ["market.history_window=full", "market.rounds=6"]
    [run] = run_config(make_config(overrides=overrides), tmp_path)
    last = [t for t in _turns(run) if t["round"] == 6][-1]["messages"][-1]["content"]
    assert "in short" not in last
    assert all(f"Round {n}: you charged" in last for n in range(1, 6))
    with pytest.raises(ConfigError, match="history_window"):
        make_config(overrides=["market.history_window=some"])


def test_show_payoffs_informed_config_plays(tmp_path):
    config = load_config(
        "configs/e5-informed.yaml",
        [
            "agents.*.model=mock/joint",
            "market.rounds=10",
            "sweep={}",
            "agents.*.prompt=system/stakes/free-time-1.md",
        ],
    )
    assert config.market.show_payoffs and config.market.history_window == "full"
    [run] = run_config(config, tmp_path)
    turns = _turns(run)
    assert "Rows: your price." in turns[0]["messages"][0]["content"]
    assert {t["phase"] for t in turns} >= {"talk", "price", "audit"}
