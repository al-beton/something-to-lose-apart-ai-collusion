# Implements: backends/reported-cost, backends/spend-asks-first, backends/spend-cap, reproducibility/manifest, runs/cheap-preset
import json
from types import SimpleNamespace

import litellm
import pytest

from collusion_lab import backends, cli, prices
from collusion_lab.cache import Cache
from collusion_lab.config import load_config
from collusion_lab.estimate import estimate
from collusion_lab.runner import RunFailed, run_config

ROUTER_MODEL = "openrouter/google/gemma-4-31b-it"
ROUTER = [f"agents.0.model={ROUTER_MODEL}", "market.talk=false"]
PRICED = [
    {"content": '{"price": 7}', "cost": 0.0012},
    {"content": '{"price": 7}', "cost": 0.0008},
]
PER_TOKEN = (1e-6, 4e-6)  # dollars per prompt token, per completion token


def read(run_dir, name):
    return [json.loads(line) for line in (run_dir / name).open()]


def manifest(run_dir):
    return json.loads((run_dir / "manifest.json").read_text())


@pytest.fixture
def price_list(monkeypatch):
    listed = {"google/gemma-4-31b-it": PER_TOKEN}
    monkeypatch.setattr(prices, "_openrouter_prices", lambda: listed)
    return listed


def test_reported_cost_asked_for_and_logged(make_config, tmp_path, fake_model):
    fake_model.replies = list(PRICED)
    [run_dir] = run_config(
        make_config(overrides=[*ROUTER, "market.rounds=2"]), tmp_path
    )
    assert fake_model.calls[0]["extra_body"]["usage"] == {"include": True}
    costs = [t["cost"] for t in read(run_dir, "timings.jsonl") if t["agent"] == "A"]
    assert costs == [0.0012, 0.0008]
    assert manifest(run_dir)["cost"] == 0.0012 + 0.0008
    assert manifest(run_dir)["unpriced_calls"] == 0


def test_reported_cost_wins_over_litellms_price(
    make_config, tmp_path, fake_model, monkeypatch
):
    monkeypatch.setattr(litellm, "completion_cost", lambda **kwargs: 99.0)
    fake_model.replies = list(PRICED)
    [run_dir] = run_config(
        make_config(overrides=[*ROUTER, "market.rounds=2"]), tmp_path
    )
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


def lab_run(tmp_path, *args, text=None):
    config = tmp_path / "c.yaml"
    config.write_text(
        text
        or "name: paid\nseeds: [0, 1]\nmarket: {rounds: 5}\nagents:\n"
        f"  - {{id: A, model: {ROUTER_MODEL}}}\n  - {{id: B, model: mock/nash}}\n"
    )
    return cli.main(["run", str(config), "--out", str(tmp_path / "runs"), *args])


def test_spend_asks_first_with_an_estimated_cost(
    tmp_path, price_list, monkeypatch, capsys
):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert lab_run(tmp_path) == 1
    out = capsys.readouterr().out
    assert "20 calls" in out and "estimated $0.00" in out


def test_spend_asks_first_says_when_a_price_is_unknown(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    lab_run(tmp_path)
    assert f"no price for {ROUTER_MODEL}" in capsys.readouterr().out


def test_spend_asks_first_estimate_within_a_quarter_of_actual(
    make_config, tmp_path, price_list, monkeypatch
):
    """A fake provider that counts four characters a token and charges the
    listed price; the estimate is made before it plays."""

    async def provider(**kwargs):
        chars = sum(len(m["content"]) for m in kwargs["messages"])
        prompt, completion = chars // 4, 100
        cost = prompt * PER_TOKEN[0] + completion * PER_TOKEN[1]
        talk = "set your price" not in kwargs["messages"][-1]["content"]
        text = (
            '{"message": "Shall we both keep prices high?"}' if talk else '{"price": 8}'
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
            usage=SimpleNamespace(
                prompt_tokens=prompt, completion_tokens=completion, cost=cost
            ),
            model="provider/model",
        )

    monkeypatch.setattr(backends, "_acompletion", provider)
    config = make_config(
        overrides=[f"agents.0.model={ROUTER_MODEL}", "market.rounds=20", "seeds=[0, 1]"]
    )
    guess = estimate(config, prices.price_for)
    actual = sum(manifest(d)["cost"] for d in run_config(config, tmp_path))
    assert abs(guess.cost - actual) / actual < 0.25


def test_spend_cap_refuses_to_start_over_the_estimate(tmp_path, price_list, capsys):
    assert lab_run(tmp_path, "-y", "--max-cost", "0.00001") == 1
    assert "over the" in capsys.readouterr().err
    assert not (tmp_path / "runs").exists()


def test_spend_cap_from_the_config_budget(tmp_path, price_list, capsys):
    text = (
        "name: paid\nseeds: [0]\nbudget: 0.00001\nmarket: {rounds: 5}\nagents:\n"
        f"  - {{id: A, model: {ROUTER_MODEL}}}\n  - {{id: B, model: mock/nash}}\n"
    )
    assert lab_run(tmp_path, "-y", text=text) == 1
    assert not (tmp_path / "runs").exists()


def test_spend_cap_stops_cleanly_once_actual_spend_passes_it(
    make_config, tmp_path, fake_model
):
    fake_model.replies = [{"content": '{"price": 7}', "cost": 0.01}] * 10
    config = make_config(overrides=[*ROUTER, "budget=0.025"])
    with pytest.raises(RunFailed, match="spend cap"):
        run_config(config, tmp_path)
    assert len(fake_model.calls) == 3


def test_cheap_preset_is_cheap_by_construction():
    config = load_config("configs/cheap.yaml")
    assert config.market.rounds == 20
    assert config.market.history_window
    assert config.budget and config.budget <= 0.30
    assert all(not a.model.startswith("mock/") for a in config.agents)
