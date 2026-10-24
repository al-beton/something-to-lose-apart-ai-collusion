# Implements: backends/any-model, backends/sampling-from-config, backends/keys-from-environment, backends/usage-logged, backends/spend-asks-first, backends/tests-never-pay, agents/retry-once
import json
import os

import pytest
from conftest import NoModelCalls

from collusion_lab import cli
from collusion_lab.config import ConfigError
from collusion_lab.runner import paid_calls, run_config

MODEL = ["agents.0.model=openrouter/openai/gpt-4.1-mini", "market.talk=false"]


def lines(run_dir, name):
    return [json.loads(line) for line in (run_dir / name).open()]


def test_any_model_goes_through_one_call_with_config_sampling(
    make_config, tmp_path, fake_model
):
    config = make_config(
        overrides=[
            *MODEL,
            "agents.0.temperature=0.2",
            "agents.0.max_tokens=99",
            "agents.0.api_base=http://localhost:8000/v1",
            "seeds=[4]",
        ]
    )
    run_config(config, tmp_path)
    call = fake_model.calls[0]
    assert call["model"] == "openrouter/openai/gpt-4.1-mini"
    assert (call["temperature"], call["max_tokens"], call["seed"]) == (0.2, 99, 4)
    assert call["api_base"] == "http://localhost:8000/v1"
    assert call["drop_params"] is True
    assert len(fake_model.calls) == 4


def test_sampling_from_config_leaves_api_base_out_when_unset(
    make_config, tmp_path, fake_model
):
    run_config(make_config(overrides=MODEL), tmp_path)
    assert "api_base" not in fake_model.calls[0]


def test_keys_from_environment_never_from_a_config(make_config):
    with pytest.raises(ConfigError, match="agents.0.api_key"):
        make_config(overrides=["agents.0.api_key=sk-nope"])


def test_usage_logged_per_turn_and_timings_kept_apart(
    make_config, tmp_path, fake_model
):
    [run_dir] = run_config(make_config(overrides=MODEL), tmp_path)
    turn = next(t for t in lines(run_dir, "turns.jsonl") if t["agent"] == "A")
    assert turn["usage"] == {"prompt_tokens": 11, "completion_tokens": 3}
    assert turn["model_version"] == "provider/model-2026-10"
    assert "latency" not in json.dumps(turn)
    timing = lines(run_dir, "timings.jsonl")[0]
    assert set(timing) >= {"round", "phase", "agent", "attempt", "seconds", "cost"}


def test_retry_once_tells_the_agent_what_was_wrong(make_config, tmp_path, fake_model):
    fake_model.replies = ["no idea", '{"price": 8}']
    [run_dir] = run_config(make_config(overrides=MODEL), tmp_path)
    first = lines(run_dir, "turns.jsonl")[0]
    assert first["used"] == {"price": 8}
    assert first["retry"] == {
        "reply": "no idea",
        "error": "There is no JSON object in the reply.",
        "usage": {"prompt_tokens": 11, "completion_tokens": 3},
        "model_version": "provider/model-2026-10",
        "reasoning": None,
        "error_kind": "no-json",
        "finish_reason": "stop",
    }
    assert "There is no JSON object" in first["messages"][-1]["content"]
    assert first["messages"][-2] == {"role": "assistant", "content": "no idea"}


def test_retry_once_then_falls_back(make_config, tmp_path, fake_model):
    fake_model.replies = ["no idea", "still no idea"]
    [run_dir] = run_config(make_config(overrides=MODEL), tmp_path)
    first = lines(run_dir, "turns.jsonl")[0]
    assert first["error"] and first["parsed"] is None
    assert first["used"] == {"price": 6}


def test_spend_asks_first_counts_paid_calls(make_config):
    assert paid_calls(make_config()) == 0
    config = make_config(overrides=[*MODEL, "seeds=[0, 1]"])
    assert paid_calls(config) == 2 * 4 * 1


def test_spend_asks_first_and_stops_without_a_yes(tmp_path, monkeypatch, capsys):
    config = tmp_path / "c.yaml"
    config.write_text(
        "name: paid\nseeds: [0]\nmarket: {rounds: 2}\nagents:\n"
        "  - {id: A, model: openai/gpt-4.1-mini}\n  - {id: B, model: mock/nash}\n"
    )
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert cli.main(["run", str(config), "--out", str(tmp_path / "runs")]) == 1
    assert "4 calls" in capsys.readouterr().out
    assert not (tmp_path / "runs").exists()


def test_tests_never_pay_unfaked_calls_fail(make_config, tmp_path):
    with pytest.raises(NoModelCalls):
        run_config(make_config(overrides=MODEL), tmp_path)


def test_keys_from_environment_read_the_working_directorys_env_file(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("COLLUSION_LAB_TEST_KEY", raising=False)
    (tmp_path / ".env").write_text("COLLUSION_LAB_TEST_KEY=from-dotenv\n")
    config = tmp_path / "c.yaml"
    config.write_text(
        "name: t\nseeds: [0]\nmarket: {rounds: 1}\nagents:\n"
        "  - {id: A, model: mock/nash}\n  - {id: B, model: mock/nash}\n"
        f"prompts_dir: {os.path.abspath('prompts')}\n"
    )
    monkeypatch.chdir(tmp_path)
    try:
        assert cli.main(["run", "c.yaml", "--out", "runs"]) == 0
        assert os.environ.get("COLLUSION_LAB_TEST_KEY") == "from-dotenv"
    finally:
        os.environ.pop("COLLUSION_LAB_TEST_KEY", None)
