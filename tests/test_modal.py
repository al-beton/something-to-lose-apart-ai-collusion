# Implements: backends/keys-from-environment, backends/self-hosted, backends/modal, backends/model-aliases
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
    "agents.0.self_hosted=true",
]
# A paid provider at its own address: not marked self-hosted.
PAID_ADDRESS = [
    "agents.0.model=openai/some-hosted-model",
    "agents.0.api_base=https://api.example-provider.com/v1",
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
        f"  - {{id: A, model: openai/mistral-small-3.2, api_base: '{ADDRESS}', "
        "self_hosted: true}\n"
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


def test_modal_config_runs_against_a_served_model(monkeypatch):
    monkeypatch.setenv("MODAL_VLLM_BASE", ADDRESS)
    config = load_config(ROOT / "configs/modal.yaml")
    server, command = _deployed(monkeypatch)
    served = command[command.index("--served-model-name") + 1]
    for agent in config.agents:
        assert agent.model == f"openai/{served}" and agent.api_base
        assert agent.api_key_env == "MODAL_VLLM_KEY"
        assert agent.self_hosted
    # vLLM logs its arguments, so the key stays in the environment; the token
    # middleware guards every route instead.
    assert "--api-key" not in command
    assert command[command.index("--middleware") + 1] == "vllm_token.require_token"
    assert server["secrets"] and server["gpu"] and server["scaledown_window"] > 0


def _deployed(monkeypatch):
    """Run deploy/modal_vllm.py against a stand-in `modal`: the settings its
    server is deployed with, and the command its start-up runs."""
    import importlib.util
    import subprocess
    import sys
    import types

    deployed = {}

    def decorator(**settings):
        deployed.update(settings)
        return lambda cls: cls

    class Chain:  # Image and Volume builders: every call returns the chain
        def __getattr__(self, name):
            return lambda *args, **kwargs: self

    modal = types.ModuleType("modal")
    modal.Image = modal.Volume = Chain()
    modal.Secret = types.SimpleNamespace(from_name=lambda name: name)
    modal.App = lambda name: types.SimpleNamespace(server=decorator)
    modal.enter = modal.exit = lambda: lambda f: f
    monkeypatch.setitem(sys.modules, "modal", modal)
    ran = []
    monkeypatch.setattr(subprocess, "Popen", lambda command: ran.append(command))
    spec = importlib.util.spec_from_file_location(
        "modal_vllm", ROOT / "deploy/modal_vllm.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.Server().start()
    return deployed, ran[0]


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


@pytest.fixture
def clock(monkeypatch):
    """Waits move a fake clock on instead of sleeping."""
    now = [1_800_000_000.0]

    async def wait(seconds):
        now[0] += seconds

    monkeypatch.setattr(backends, "_sleep", wait)
    monkeypatch.setattr(backends, "_now", lambda: now[0])
    return now


def starting(n):
    import litellm

    return [
        litellm.ServiceUnavailableError("no containers yet", "openai", "m")
        for _ in range(n)
    ]


def test_self_hosted_waits_out_a_cold_start(make_config, tmp_path, fake_model, clock):
    fake_model.replies = starting(30)  # about 7 minutes of 503s at 15 s apart
    config = make_config(overrides=[*SELF_HOSTED, "market.rounds=1"])
    [run_dir] = run_config(config, tmp_path)
    timings = [json.loads(line) for line in (run_dir / "timings.jsonl").open()]
    assert len(timings[0]["retries"]) == 30


def test_self_hosted_cold_start_has_a_deadline(
    make_config, tmp_path, fake_model, clock
):
    from collusion_lab.runner import RunFailed

    fake_model.replies = starting(200)  # longer than the 20-minute start-up limit
    config = make_config(overrides=[*SELF_HOSTED, "market.rounds=1"])
    with pytest.raises(RunFailed, match="ServiceUnavailable"):
        run_config(config, tmp_path)


def test_hosted_models_keep_their_usual_retries(
    make_config, tmp_path, fake_model, clock
):
    from collusion_lab.runner import RunFailed

    fake_model.replies = starting(30)
    hosted = ["agents.0.model=openrouter/openai/gpt-4.1-mini", "market.rounds=1"]
    with pytest.raises(RunFailed, match="gave up after 6 tries"):
        run_config(make_config(overrides=hosted), tmp_path)


def test_modal_token_guards_every_route_but_health(monkeypatch):
    import asyncio
    import importlib.util
    import sys
    import types

    responses = types.ModuleType("starlette.responses")
    responses.JSONResponse = lambda body, status_code: ("refused", status_code)
    monkeypatch.setitem(sys.modules, "starlette.responses", responses)
    monkeypatch.setenv("VLLM_API_KEY", "modal-token-123")
    spec = importlib.util.spec_from_file_location(
        "vllm_token", ROOT / "deploy/vllm_token.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    async def call_next(request):
        return "served"

    def ask(path, token=None):
        headers = {"authorization": f"Bearer {token}"} if token else {}
        request = types.SimpleNamespace(
            url=types.SimpleNamespace(path=path), headers=headers
        )
        return asyncio.run(module.require_token(request, call_next))

    assert ask("/invocations") == ("refused", 401)
    assert ask("/inference/v1/generate", "wrong") == ("refused", 401)
    assert ask("/v1/chat/completions", "modal-token-123") == "served"
    assert ask("/invocations", "modal-token-123") == "served"
    assert ask("/health") == "served"


def test_self_hosted_only_when_marked_a_paid_address_is_estimated(make_config):
    from collusion_lab.estimate import estimate

    def price_for(model):
        return (1e-6, 4e-6)

    paid = estimate(make_config(overrides=PAID_ADDRESS), price_for)
    assert paid.self_hosted == [] and paid.cost > 0
    hosted = estimate(make_config(overrides=SELF_HOSTED), price_for)
    assert hosted.self_hosted == ["openai/mistral-small-3.2"] and hosted.cost == 0


def test_self_hosted_only_when_marked_a_paid_address_counts_against_the_cap(
    make_config, tmp_path, fake_model, monkeypatch
):
    monkeypatch.setattr(backends, "_cost", lambda response: 1.0)
    [run_dir] = run_config(make_config(overrides=PAID_ADDRESS), tmp_path)
    timings = [json.loads(line) for line in (run_dir / "timings.jsonl").open()]
    assert {t["cost"] for t in timings if t["agent"] == "A"} == {1.0}


def test_self_hosted_only_when_marked_a_paid_address_keeps_usual_retries(
    make_config, tmp_path, fake_model, clock
):
    from collusion_lab.runner import RunFailed

    fake_model.replies = starting(30)
    with pytest.raises(RunFailed, match="gave up after 6 tries"):
        run_config(make_config(overrides=[*PAID_ADDRESS, "market.rounds=1"]), tmp_path)


def test_self_hosted_needs_its_own_address(make_config):
    from collusion_lab.config import ConfigError

    with pytest.raises(ConfigError, match="self_hosted"):
        make_config(overrides=["agents.0.self_hosted=true"])


def test_modal_pinned_serves_one_revision_at_a_stated_dtype(monkeypatch):
    monkeypatch.setenv("REVISION", "0123abcd")
    _, command = _deployed(monkeypatch)
    for flag, value in (
        ("--revision", "0123abcd"),
        ("--dtype", "bfloat16"),
        ("--max-model-len", "16384"),
    ):
        assert command[command.index(flag) + 1] == value


def test_modal_pinned_revision_looked_up_at_deploy(monkeypatch):
    import io
    import urllib.request

    monkeypatch.delenv("REVISION", raising=False)
    asked = []

    def hub(url, timeout):
        asked.append(url)
        return io.BytesIO(json.dumps({"sha": "feedface"}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", hub)
    _, command = _deployed(monkeypatch)
    assert command[command.index("--revision") + 1] == "feedface"
    assert asked == [
        "https://huggingface.co/api/models/mistralai/Mistral-Small-3.2-24B-Instruct-2506"
    ]

    def down(url, timeout):
        raise OSError("no network")

    monkeypatch.setattr(urllib.request, "urlopen", down)
    with pytest.raises(RuntimeError, match="REVISION"):
        _deployed(monkeypatch)


def test_modal_pinned_provenance_behind_the_token(monkeypatch, tmp_path):
    import asyncio
    import importlib.util
    import sys
    import types

    written = tmp_path / "provenance.json"
    monkeypatch.setenv("PROVENANCE_FILE", str(written))
    monkeypatch.setenv("REVISION", "0123abcd")
    monkeypatch.setenv("DEPLOY_COMMIT", "c0ffee")
    _deployed(monkeypatch)
    told = json.loads(written.read_text())
    assert told["revision"] == "0123abcd" and told["deploy_commit"] == "c0ffee"
    assert told["dtype"] == "bfloat16" and told["max_model_len"] == 16384
    assert {"model", "served_name", "gpu", "vllm"} <= told.keys()

    responses = types.ModuleType("starlette.responses")
    responses.JSONResponse = lambda body, status_code: (body, status_code)
    monkeypatch.setitem(sys.modules, "starlette.responses", responses)
    monkeypatch.setenv("VLLM_API_KEY", "modal-token-123")
    spec = importlib.util.spec_from_file_location(
        "vllm_token", ROOT / "deploy/vllm_token.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    async def call_next(request):
        return "served"

    def ask(token=None):
        headers = {"authorization": f"Bearer {token}"} if token else {}
        request = types.SimpleNamespace(
            url=types.SimpleNamespace(path="/provenance"), headers=headers
        )
        return asyncio.run(module.require_token(request, call_next))

    assert ask()[1] == 401
    assert ask("modal-token-123") == (told, 200)


def test_modal_pinned_run_records_what_served_it(
    make_config, tmp_path, fake_model, monkeypatch
):
    from collusion_lab import manifest

    told = {"revision": "0123abcd", "vllm": "0.21.0", "gpu": "H100"}
    asked = []

    def serving(url, headers):
        asked.append((url, headers))
        return told

    monkeypatch.setattr(manifest, "_get_json", serving)
    monkeypatch.setenv("MODAL_KEY", "modal-token-123")
    overrides = [*SELF_HOSTED, "agents.0.api_key_env=MODAL_KEY"]
    [run_dir] = run_config(make_config(overrides=overrides), tmp_path)
    record = json.loads((run_dir / "manifest.json").read_text())
    assert record["serving"] == {"A": told}
    assert asked == [
        (
            "https://example--collusion-lab-vllm-serve.modal.run/provenance",
            {"Authorization": "Bearer modal-token-123"},
        )
    ]
    assert "modal-token-123" not in (run_dir / "manifest.json").read_text()


def test_modal_pinned_seed_passed_to_the_server(make_config, tmp_path, fake_model):
    run_config(make_config(overrides=[*SELF_HOSTED, "seeds=[7]"]), tmp_path)
    assert {call["seed"] for call in fake_model.calls} == {7}
