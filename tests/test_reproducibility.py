# Implements: reproducibility/response-cache, reproducibility/cache-modes, reproducibility/manifest
import hashlib
import json
from pathlib import Path

from collusion_lab.cache import Cache
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
    assert set(manifest["prompts"]) >= {"phase/price.md", "phase/retry.md"}
    assert set(manifest["code"]) == {"commit", "dirty"}
    assert {"python", "collusion-lab", "litellm", "pyyaml"} <= set(manifest["packages"])
    assert manifest["models"] == {"A": ["provider/model-2026-10"]}
    assert manifest["calls"] == 4
    assert manifest["cache"] == {"hits": 4, "misses": 0}
    assert manifest["tokens"] == {"prompt": 44, "completion": 12}
    assert manifest["cost"] == 0
    assert manifest["started"] <= manifest["finished"]
