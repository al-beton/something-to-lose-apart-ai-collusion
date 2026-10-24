# Implements: runs/one-config, runs/overrides
import pytest

from collusion_lab.config import ConfigError, load_config


def test_one_config_sets_market_agents_and_seeds():
    config = load_config("configs/smoke.yaml")
    assert config.name == "smoke"
    assert config.seeds == [0, 1, 2]
    assert config.market.rounds == 10
    assert [a.id for a in config.agents] == ["A", "B"]
    assert config.agents[0].model.startswith("mock/")
    assert config.agents[0].prompt == "system/neutral.md"


def test_one_config_rejects_unknown_keys(make_config):
    with pytest.raises(ConfigError, match="roundz"):
        make_config("name: t\nseeds: [0]\nmarket: {roundz: 3}\nagents: []\n")


def test_overrides_change_any_value(make_config):
    config = make_config(
        overrides=["market.rounds=3", "agents.1.model=mock/random", "seeds=[5, 6]"]
    )
    assert config.market.rounds == 3
    assert config.agents[1].model == "mock/random"
    assert config.seeds == [5, 6]


def test_overrides_reject_paths_that_dont_exist(make_config):
    with pytest.raises(ConfigError, match="market.nope"):
        make_config(overrides=["market.nope=1"])
