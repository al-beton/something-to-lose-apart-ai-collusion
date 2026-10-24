# Implements: backends/keys-from-environment, backends/self-hosted, backends/modal
import json
import re
from pathlib import Path

import pytest

from collusion_lab import backends, cli
from collusion_lab.config import load_config
from collusion_lab.runner import run_config

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "https://example--collusion-lab-vllm-serve.modal.run/v1"
SELF_HOSTED = [
    "agents.0.model=openai/mistral-small-3.2",
    f"agents.0.api_base={ADDRESS}",
]


def run_text(run_dir):
    return "".join(p.read_text() for p in run_dir.iterdir() if p.is_file())


def test_keys_from_environment_only_the_named_key_goes_to_an_address(
    make_config, tmp_path, fake_model, monkeypatch
):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-provider-key")
    monkeypatch.setenv("MODAL_VLLM_KEY", "modal-token-123")
    named = make_config(overrides=[*SELF_HOSTED, "agents.0.api_key_env=MODAL_VLLM_KEY"])
    [run_dir] = run_config(named, tmp_path / "named")
    assert {c["api_key"] for c in fake_model.calls} == {"modal-token-123"}
    assert "modal-token-123" not in run_text(run_dir)
    fake_model.calls.clear()
    run_config(make_config(overrides=SELF_HOSTED), tmp_path / "unnamed")
    keys = {c.get("api_key") for c in fake_model.calls}
    assert "sk-provider-key" not in keys and None not in keys


def test_keys_from_environment_missing_named_key_stops_the_run(
    make_config, tmp_path, fake_model, monkeypatch
):
    monkeypatch.delenv("MODAL_VLLM_KEY", raising=False)
    config = make_config(
        overrides=[*SELF_HOSTED, "agents.0.api_key_env=MODAL_VLLM_KEY"]
    )
    with pytest.raises(Exception, match="MODAL_VLLM_KEY"):
        run_config(config, tmp_path)
    assert not fake_model.calls


def test_self_hosted_says_billed_by_gpu_time(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    config = tmp_path / "c.yaml"
    config.write_text(
        "name: hosted\nseeds: [0]\nmarket: {rounds: 3}\nagents:\n"
        f"  - {{id: A, model: openai/mistral-small-3.2, api_base: '{ADDRESS}'}}\n"
        "  - {id: B, model: mock/nash}\n"
    )
    assert cli.main(["run", str(config), "--out", str(tmp_path / "runs")]) == 1
    out = capsys.readouterr().out
    assert "self-hosted" in out and "GPU time" in out
    assert "$0.0000" not in out and "no price" not in out


def test_self_hosted_costs_nothing_against_the_cap(
    make_config, tmp_path, fake_model, monkeypatch
):
    monkeypatch.setattr(backends, "_cost", lambda response: 1.0)
    [run_dir] = run_config(make_config(overrides=SELF_HOSTED), tmp_path)
    timings = [json.loads(line) for line in (run_dir / "timings.jsonl").open()]
    assert {t["cost"] for t in timings if t["agent"] == "A"} == {None}


def test_modal_config_runs_against_a_served_model():
    config = load_config(ROOT / "configs/modal.yaml")
    serve = (ROOT / "deploy/modal_vllm.py").read_text()
    for agent in config.agents:
        assert agent.model.startswith("openai/") and agent.api_base
        assert agent.api_key_env == "MODAL_VLLM_KEY"
        assert agent.model.removeprefix("openai/") in serve
    assert re.search(r"--api-key", serve) and "Secret.from_name" in serve
    assert "scaledown_window" in serve and "gpu=" in serve


def test_modal_readme_says_how_to_set_up_deploy_run_and_tear_down():
    readme = (ROOT / "README.md").read_text()
    match = re.search(
        r"^## Running on Modal\n(.*?)(?=^## |\Z)", readme, re.MULTILINE | re.DOTALL
    )
    assert match, "README has no '## Running on Modal' section."
    steps = match.group(1)
    order = [
        "modal setup",
        "modal secret create",
        "modal deploy deploy/modal_vllm.py",
        "lab run configs/modal.yaml",
        "modal app stop",
    ]
    places = [steps.find(step) for step in order]
    assert -1 not in places and places == sorted(places), dict(
        zip(order, places, strict=True)
    )
    assert "GPU" in steps and "minutes" in steps


def test_keys_from_environment_never_echoed_into_run_files(
    make_config, tmp_path, fake_model, monkeypatch
):
    import litellm

    from collusion_lab.runner import RunFailed

    monkeypatch.setenv("MODAL_VLLM_KEY", "modal-token-123")
    monkeypatch.setattr(backends, "_sleep", lambda seconds: asyncio_sleep0())
    echoed = "Incorrect API key provided: modal-token-123"
    fake_model.replies = [
        litellm.InternalServerError(echoed, "openai", "mistral-small-3.2"),
        litellm.AuthenticationError(echoed, "openai", "mistral-small-3.2"),
    ]
    config = make_config(
        overrides=[*SELF_HOSTED, "agents.0.api_key_env=MODAL_VLLM_KEY"]
    )
    with pytest.raises(RunFailed) as stopped:
        run_config(config, tmp_path)
    assert "modal-token-123" not in str(stopped.value) and "***" in str(stopped.value)
    written = "".join(p.read_text() for p in tmp_path.rglob("*") if p.is_file())
    assert "modal-token-123" not in written and "***" in written


async def asyncio_sleep0():
    import asyncio

    await asyncio.sleep(0)
