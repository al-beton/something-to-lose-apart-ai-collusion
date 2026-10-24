# Implements: reproducibility/response-cache, reproducibility/cache-modes, reproducibility/manifest
import asyncio
import hashlib
import json
from pathlib import Path

from collusion_lab.backends import Reply
from collusion_lab.cache import Cache, CachedBackend
from collusion_lab.runner import run_config

MODEL = ["agents.0.model=openrouter/openai/gpt-4.1-mini", "market.talk=false"]


def play(config, out, cache):
    [run_dir] = run_config(config, out, cache=cache)
    return run_dir


def test_response_cache_replays_a_run_exactly_without_calling(
    make_config, tmp_path, fake_model
):
    config = make_config(overrides=MODEL)
    cache = Cache(tmp_path / "cache.sqlite")
    first = play(config, tmp_path / "1", cache)
    calls = len(fake_model.calls)
    fake_model.replies = ['{"price": 3}'] * 50
    again = play(config, tmp_path / "2", Cache(tmp_path / "cache.sqlite"))
    assert len(fake_model.calls) == calls
    assert (first / "turns.jsonl").read_bytes() == (again / "turns.jsonl").read_bytes()


def test_response_cache_misses_when_the_seed_changes(make_config, tmp_path, fake_model):
    cache = Cache(tmp_path / "cache.sqlite")
    play(make_config(overrides=MODEL), tmp_path / "1", cache)
    calls = len(fake_model.calls)
    play(make_config(overrides=[*MODEL, "seeds=[1]"]), tmp_path / "2", cache)
    assert len(fake_model.calls) == 2 * calls


def test_cache_modes_refresh_calls_again_and_stores_the_new_reply(
    make_config, tmp_path, fake_model
):
    config = make_config(overrides=MODEL)
    path = tmp_path / "cache.sqlite"
    play(config, tmp_path / "1", Cache(path))
    fake_model.replies = ['{"price": 3}'] * 4
    refreshed = play(config, tmp_path / "2", Cache(path, mode="refresh"))
    replayed = play(config, tmp_path / "3", Cache(path))
    assert (refreshed / "turns.jsonl").read_bytes() == (
        replayed / "turns.jsonl"
    ).read_bytes()
    assert '"price": 3' in (replayed / "turns.jsonl").read_text()


def test_cache_modes_off_neither_reads_nor_stores(make_config, tmp_path, fake_model):
    config = make_config(overrides=MODEL)
    path = tmp_path / "cache.sqlite"
    play(config, tmp_path / "1", Cache(path, mode="off"))
    calls = len(fake_model.calls)
    play(config, tmp_path / "2", Cache(path))
    assert len(fake_model.calls) == 2 * calls


def test_cache_modes_mock_agents_skip_the_cache(make_config, tmp_path):
    cache = Cache(tmp_path / "cache.sqlite")
    run_dir = play(make_config(), tmp_path / "1", cache)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["cache"] == {"hits": 0, "misses": 0}


def test_manifest_records_what_produced_the_run(make_config, tmp_path, fake_model):
    cache = Cache(tmp_path / "cache.sqlite")
    config = make_config(overrides=MODEL)
    play(config, tmp_path / "1", cache)
    run_dir = play(config, tmp_path / "2", cache)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["config"]["agents"][0]["model"] == MODEL[0].split("=")[1]
    neutral = Path("prompts/system/neutral.md").read_bytes()
    assert (
        manifest["prompts"]["system/neutral.md"] == hashlib.sha256(neutral).hexdigest()
    )
    assert set(manifest["prompts"]) == {"system/neutral.md", "phase/price.md"}
    assert set(manifest["code"]) == {"commit", "dirty"}
    assert {"python", "collusion-lab", "litellm", "pyyaml"} <= set(manifest["packages"])
    assert manifest["models"] == {"A": ["provider/model-2026-10"]}
    assert manifest["calls"] == 4
    assert manifest["cache"] == {"hits": 4, "misses": 0}
    assert manifest["tokens"] == {"prompt": 44, "completion": 12}
    assert manifest["cost"] == 0
    assert manifest["started"] <= manifest["finished"]


def custom_prompts(tmp_path, *phases):
    """A prompts folder with a system prompt that doesn't name the agent."""
    folder = tmp_path / "prompts"
    (folder / "system").mkdir(parents=True)
    (folder / "system" / "plain.md").write_text("Set prices.\n")
    for name in phases:
        (folder / name).parent.mkdir(exist_ok=True)
        (folder / name).write_text(Path("prompts", name).read_text())
    return folder


def test_response_cache_replays_agents_asking_identical_questions(
    make_config, tmp_path, fake_model
):
    folder = custom_prompts(tmp_path, "phase/price.md", "phase/retry.md")
    config = make_config(
        overrides=[
            "agents.0.model=openai/gpt-4.1-mini",
            "agents.1.model=openai/gpt-4.1-mini",
            "agents.0.prompt=system/plain.md",
            "agents.1.prompt=system/plain.md",
            f"prompts_dir={folder}",
            "market.talk=false",
            "market.rounds=1",
        ]
    )
    fake_model.replies = ['{"price": 3}', '{"price": 4}']
    path = tmp_path / "cache.sqlite"
    first = play(config, tmp_path / "1", Cache(path))
    again = play(config, tmp_path / "2", Cache(path))
    assert (first / "turns.jsonl").read_bytes() == (again / "turns.jsonl").read_bytes()


def test_manifest_hashes_only_the_prompts_the_run_used(make_config, tmp_path):
    folder = custom_prompts(tmp_path, "phase/price.md")
    config = make_config(
        overrides=[
            "agents.0.prompt=system/plain.md",
            "agents.1.prompt=system/plain.md",
            f"prompts_dir={folder}",
            "market.talk=false",
        ]
    )
    run_dir = play(config, tmp_path / "1", None)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert set(manifest["prompts"]) == {"system/plain.md", "phase/price.md"}


def test_manifest_keeps_unknown_costs_unknown(make_config, tmp_path, fake_model):
    config = make_config(overrides=MODEL)
    cache = Cache(tmp_path / "cache.sqlite")
    fresh = json.loads(
        (play(config, tmp_path / "1", cache) / "manifest.json").read_text()
    )
    replay = json.loads(
        (play(config, tmp_path / "2", cache) / "manifest.json").read_text()
    )
    assert (fresh["cost"], fresh["unpriced_calls"]) == (None, 4)
    assert (replay["cost"], replay["unpriced_calls"]) == (0, 0)


def test_manifest_code_version_is_the_labs_own(make_config, tmp_path, monkeypatch):
    import subprocess

    lab = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    config = make_config(overrides=[f"prompts_dir={Path('prompts').resolve()}"])
    monkeypatch.chdir(tmp_path)
    run_dir = play(config, tmp_path / "1", None)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["code"]["commit"] == lab


def test_response_cache_shares_one_call_between_identical_requests_in_flight(
    tmp_path,
):
    class SlowModel:
        model, api_base, calls = "openai/gpt-4.1-mini", None, 0

        async def complete(self, messages, **kwargs):
            SlowModel.calls += 1
            await asyncio.sleep(0.01)
            return Reply(text=f'{{"price": {SlowModel.calls}}}')

    cache = Cache(tmp_path / "cache.sqlite")
    arms = [CachedBackend(SlowModel(), cache) for _ in range(2)]
    ask = {
        "context": {"attempt": 1, "me": "A"},
        "temperature": 0.7,
        "max_tokens": 50,
        "seed": 0,
    }

    async def both():
        return await asyncio.gather(*(arm.complete([], **ask) for arm in arms))

    first, second = asyncio.run(both())
    assert SlowModel.calls == 1
    assert first.text == second.text
    assert asyncio.run(arms[0].complete([], **ask)).text == first.text
