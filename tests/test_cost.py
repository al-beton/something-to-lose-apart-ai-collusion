# Implements: backends/reported-cost, backends/spend-asks-first, backends/spend-cap, reproducibility/manifest, runs/cheap-preset
import asyncio
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
SAID = (  # a talk message as long as real ones run
    "Our prices have been steady and we both earned well; I plan to stay at 8 "
    "this round and expect you will too, rather than start cutting each other."
)


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
    out, cache = str(tmp_path / "runs"), str(tmp_path / "cache.sqlite")
    return cli.main(["run", str(config), "--out", out, "--cache-path", cache, *args])


def test_spend_asks_first_with_an_estimated_cost(
    tmp_path, price_list, monkeypatch, capsys
):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert lab_run(tmp_path) == 1
    out = capsys.readouterr().out
    # Nothing cached yet: every reply is taken at its max_tokens, the most.
    assert "20 calls" in out and "estimated $0.0173" in out
    assert "a typical reply for its reasoning level, for 20 calls" in out


def test_spend_asks_first_says_when_a_price_is_unknown(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    lab_run(tmp_path)
    assert f"no price for {ROUTER_MODEL}" in capsys.readouterr().out


def test_spend_asks_first_estimate_within_a_quarter_of_actual(
    make_config, tmp_path, price_list, monkeypatch
):
    """A fake provider that counts four characters a token and charges the
    listed price. Before it plays, the estimate is an upper bound; once its
    replies are cached, their observed lengths bring it within a quarter."""

    async def provider(**kwargs):
        chars = sum(len(m["content"]) for m in kwargs["messages"])
        prompt, completion = chars // 4, 100
        cost = prompt * PER_TOKEN[0] + completion * PER_TOKEN[1]
        talk = "set your price" not in kwargs["messages"][-1]["content"]
        text = json.dumps({"message": SAID}) if talk else '{"price": 8}'
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
            usage=SimpleNamespace(
                prompt_tokens=prompt, completion_tokens=completion, cost=cost
            ),
            model="provider/model",
        )

    monkeypatch.setattr(backends, "_acompletion", provider)
    both = [f"agents.{i}.model={ROUTER_MODEL}" for i in (0, 1)]
    config = make_config(overrides=[*both, "market.rounds=20", "seeds=[0, 1]"])
    bound = estimate(config, prices.price_for)
    cache = Cache(tmp_path / "cache.sqlite")
    actual = sum(manifest(d)["cost"] for d in run_config(config, tmp_path, cache))
    guess = estimate(config, prices.price_for, cache.observed())
    assert bound.cost >= actual
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


def test_spend_cap_rechecked_after_a_rate_limit_wait(
    make_config, tmp_path, fake_model, monkeypatch
):
    """A waits out a rate limit while B's reply passes the cap: A must not call."""
    import httpx

    clock = [1_800_000_000.0]

    async def wait(seconds):
        await asyncio.sleep(0)  # let B answer meanwhile
        clock[0] += seconds

    monkeypatch.setattr(backends, "_sleep", wait)
    monkeypatch.setattr(backends, "_now", lambda: clock[0])
    response = httpx.Response(
        429,
        headers={"Retry-After": "30"},
        request=httpx.Request("POST", "https://example.test"),
    )
    limited = litellm.RateLimitError(
        message="Rate limit exceeded",
        llm_provider="openrouter",
        model=ROUTER_MODEL,
        response=response,
    )
    fake_model.replies = [limited, {"content": '{"price": 7}', "cost": 0.05}]
    both = [f"agents.{i}.model={ROUTER_MODEL}" for i in (0, 1)]
    config = make_config(overrides=[*both, "market.talk=false", "budget=0.01"])
    with pytest.raises(RunFailed, match="spend cap"):
        run_config(config, tmp_path)
    assert len(fake_model.calls) == 2


def test_spend_cap_warns_when_a_model_has_no_price(tmp_path, fake_model, capsys):
    lab_run(tmp_path, "-y", "--max-cost", "1", "--set", "market.rounds=1")
    err = capsys.readouterr().err
    assert f"no price for {ROUTER_MODEL}" in err and "can't be enforced" in err
