# Implements: runs/explore, runs/price-premium
import pytest

from collusion_lab import cli, explore
from collusion_lab.config import ConfigError
from collusion_lab.runner import run_config
from collusion_lab.summary import summarize

SHORT = ["market.rounds=4"]


def test_price_premium_is_zero_at_nash_and_one_at_the_cartel(make_config, tmp_path):
    run_config(make_config(), tmp_path / "nash")
    [nash] = summarize(tmp_path / "nash")
    assert (nash["premium"], nash["% above Nash"]) == (0, 0)
    joint = ["agents.0.model=mock/joint", "agents.1.model=mock/joint"]
    run_config(make_config(overrides=joint), tmp_path / "joint")
    [cartel] = summarize(tmp_path / "joint")
    assert cartel["premium"] == 1  # default market: Nash 6, joint 9
    assert cartel["% above Nash"] == 50


def test_price_premium_counts_the_model_firm_against_a_script(
    make_config, tmp_path, fake_model
):
    # The fake model prices at 7 against the scripted proposer's 9.
    mixed = ["agents.0.model=fake/llm", "agents.1.model=mock/proposer"]
    run_config(make_config(overrides=mixed), tmp_path)
    [row] = summarize(tmp_path)
    assert row["premium"] == round((7 - 6) / (9 - 6), 3)


def test_explore_model_names_are_short():
    assert explore.agent_fields("gemma") == {
        "model": "openrouter/google/gemma-4-31b-it"
    }
    assert explore.agent_fields("gpt")["model"] == "openrouter/openai/gpt-4.1-mini"
    assert (
        explore.agent_fields("haiku")["model"]
        == "openrouter/anthropic/claude-haiku-5.5"
    )
    assert "mistral-small" in explore.agent_fields("mistral")["model"]
    modal = explore.agent_fields("modal-mistral")
    assert modal["self_hosted"] is True and modal["api_base"]
    assert explore.agent_fields("mock/nash") == {"model": "mock/nash"}
    with pytest.raises(ConfigError, match="gemma"):
        explore.agent_fields("gemini-ultra")


def test_explore_builds_every_combination_of_settings_and_models():
    levers = {"temptation": ["low", "high"], "rule": ["none", "ban"]}
    configs = explore.build(levers, ["mock/nash", "mock/joint"], seeds=2)
    assert len(configs) == 8
    labels = [c.labels for c in configs]
    assert {"temptation": "high", "rule": "ban", "model": "mock/joint"} in labels
    high_ban = next(
        c
        for c in configs
        if c.labels["temptation"] == "high" and c.labels["rule"] == "ban"
    )
    assert high_ban.market.c == 1.8 and high_ban.seeds == [0, 1]
    assert high_ban.conditions["instruction"].enabled
    assert high_ban.conditions["instruction"].prompt == "conditions/no-collusion.md"
    low_none = next(
        c
        for c in configs
        if c.labels["temptation"] == "low" and c.labels["rule"] == "none"
    )
    assert low_none.market.c == 1.0 and "instruction" not in low_none.conditions
    assert len({c.slug for c in configs}) == 8


def test_explore_levers_reuse_the_existing_presets():
    def one(lever, setting, model="mock/nash"):
        [config] = explore.build({lever: [setting]}, [model], seeds=1)
        return config

    assert one("rival", "proposer").agents[1].model == "mock/proposer"
    assert one("rival", "solicitor").agents[1].model == "mock/solicitor"
    assert one("rival", "gpt").agents[1].model == "openrouter/openai/gpt-4.1-mini"
    assert one("rival", "same").agents[1].model == "mock/nash"
    assert one("rule", "illegal").agents[0].prompt == "system/stakes/illegal-1.md"
    assert (
        one("stake", "termination").agents[1].prompt == "system/stakes/termination-1.md"
    )
    assert one("stake", "free-time").conditions["free_time"].enabled
    assert one("oversight", "outage").conditions["outage"].enabled
    audited = one("oversight", "audit").conditions["audit"]
    assert audited.enabled and not audited.end and audited.matched
    for lever, settings in explore.LEVERS.items():
        for setting in settings:
            one(lever, setting)  # every preset builds a valid config
    with pytest.raises(ConfigError, match="temptation.*low"):
        one("temptation", "lukewarm")
    with pytest.raises(ConfigError, match="levers"):
        one("weather", "sunny")


def test_explore_plays_and_ends_with_a_premium_table_and_chart(tmp_path, capsys):
    out = tmp_path / "explore"
    args = [
        "explore",
        "--lever",
        "temptation=low,high",
        "--models",
        "mock/nash,mock/joint",
    ]
    args += ["--seeds", "1", "--out", str(out), *[f"--set={s}" for s in SHORT]]
    assert cli.main(args) == 0
    text = capsys.readouterr().out
    assert "| temptation | model |" in text and "premium" in text
    assert (out / "premium.svg").exists()
    svg = (out / "premium.svg").read_text()
    assert "mock/nash" in svg and "mock/joint" in svg and "<polyline" in svg
    assert f"lab report {out}" in text


def test_explore_asks_before_spending(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    out = tmp_path / "explore"
    args = ["explore", "--lever", "rule=none,ban", "--models", "gpt", "--seeds", "1"]
    assert cli.main([*args, "--out", str(out)]) == 1
    assert "calls to paid models" in capsys.readouterr().out
    assert not out.exists()
