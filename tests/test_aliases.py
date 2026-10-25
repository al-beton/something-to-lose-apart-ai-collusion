# Implements: backends/model-aliases
import pytest

from collusion_lab.config import ConfigError, expand

MODAL = "https://example--collusion-lab-vllm-server.us-east.modal.direct/v1"


def test_model_aliases_name_the_usual_models(make_config):
    config = make_config(overrides=["agents.0.model=gemma", "agents.1.model=haiku"])
    assert [a.model for a in config.agents] == [
        "openrouter/google/gemma-4-31b-it",
        "openrouter/anthropic/claude-haiku-5.5",
    ]
    assert all(a.api_base is None and not a.self_hosted for a in config.agents)


def test_model_aliases_modal_mistral_reads_its_address(make_config, monkeypatch):
    monkeypatch.setenv("MODAL_VLLM_BASE", MODAL)
    [agent, _] = make_config(overrides=["agents.0.model=modal-mistral"]).agents
    assert agent.model == "openai/mistral-small-3.2"
    assert (agent.api_base, agent.api_key_env, agent.self_hosted) == (
        MODAL,
        "MODAL_VLLM_KEY",
        True,
    )


def test_model_aliases_modal_mistral_needs_its_address(make_config, monkeypatch):
    monkeypatch.delenv("MODAL_VLLM_BASE", raising=False)
    with pytest.raises(ConfigError, match="MODAL_VLLM_BASE"):
        make_config(overrides=["agents.0.model=modal-mistral"])


def test_model_aliases_swap_cleanly_in_a_sweep(make_config, monkeypatch):
    monkeypatch.setenv("MODAL_VLLM_BASE", MODAL)
    config = make_config(
        overrides=[
            "agents.0.model=modal-mistral",
            "sweep={agents.0.model: [modal-mistral, gpt, mistral]}",
        ]
    )
    agents = {c.labels["model"]: c.agents[0] for c in expand(config)}
    assert agents["modal-mistral"].api_base == MODAL
    for name in ("gpt", "mistral"):
        hosted = agents[name]
        assert hosted.model.startswith("openrouter/")
        assert hosted.api_base is None and not hosted.self_hosted
        assert hosted.api_key_env is None
