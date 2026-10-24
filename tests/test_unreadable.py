# Implements: agents/unreadable-explained, agents/json-mode, runs/fallback-rates
import json

import pytest

from collusion_lab import cli
from collusion_lab.cache import Cache
from collusion_lab.report import build_report
from collusion_lab.runner import run_config
from collusion_lab.summary import flagged_runs, reply_rates

MODEL_NAME = "openrouter/qwen/qwen3.8-flash"
MODEL = [f"agents.0.model={MODEL_NAME}", "market.talk=false"]
GOOD = '{"price": 7}'


def first_turn(run_dir):
    turns = [json.loads(line) for line in (run_dir / "turns.jsonl").open()]
    return next(t for t in turns if t["agent"] == "A")


@pytest.mark.parametrize(
    ("reply", "kind"),
    [
        (
            {"content": '{"scratchpad": "Let me think', "finish_reason": "length"},
            "truncated",
        ),
        ({"content": "   "}, "empty"),
        ({"content": "I pick seven."}, "no-json"),
        ({"content": '{"cost": 7}'}, "missing-field"),
        ({"content": '{"price": 40}'}, "off-grid"),
    ],
)
def test_unreadable_explained_for_each_kind(
    make_config, tmp_path, fake_model, reply, kind
):
    fake_model.replies = [reply, GOOD]
    [run_dir] = run_config(make_config(overrides=MODEL), tmp_path)
    turn = first_turn(run_dir)
    assert turn["retry"]["error_kind"] == kind
    assert turn["retry"]["finish_reason"] == reply.get("finish_reason", "stop")
    assert (turn["error_kind"], turn["finish_reason"]) == (None, "stop")


def test_unreadable_explained_cut_off_reply_asked_to_keep_it_short(
    make_config, tmp_path, fake_model
):
    fake_model.replies = [{"content": '{"price"', "finish_reason": "length"}, GOOD]
    [run_dir] = run_config(make_config(overrides=MODEL), tmp_path)
    assert "keep it short" in first_turn(run_dir)["messages"][-1]["content"]


def test_unreadable_explained_when_the_turn_falls_back(
    make_config, tmp_path, fake_model
):
    fake_model.replies = ["nope", ""]
    [run_dir] = run_config(make_config(overrides=MODEL), tmp_path)
    turn = first_turn(run_dir)
    assert (turn["retry"]["error_kind"], turn["error_kind"]) == ("no-json", "empty")


def test_json_mode_asks_the_provider_for_json(make_config, tmp_path, fake_model):
    run_config(make_config(overrides=[*MODEL, "agents.0.json_mode=true"]), tmp_path)
    assert fake_model.calls[0]["response_format"] == {"type": "json_object"}


def test_json_mode_off_by_default_and_part_of_the_cache_key(
    make_config, tmp_path, fake_model
):
    cache = Cache(tmp_path / "cache.sqlite")
    run_config(make_config(overrides=MODEL), tmp_path / "1", cache)
    assert "response_format" not in fake_model.calls[0]
    calls = len(fake_model.calls)
    json_mode = make_config(overrides=[*MODEL, "agents.0.json_mode=true"])
    run_config(json_mode, tmp_path / "2", cache)
    assert len(fake_model.calls) == 2 * calls


@pytest.fixture
def bumpy(make_config, tmp_path, fake_model):
    """Round 1 falls back after two unreadable replies; round 2 recovers."""
    fake_model.replies = ["nope", {"content": '{"price', "finish_reason": "length"}]
    fake_model.replies += ["nope", GOOD]
    run_config(make_config(overrides=MODEL), tmp_path)
    return tmp_path


def test_fallback_rates_per_model_with_reasons(bumpy):
    rates = {r["model"]: r for r in reply_rates(bumpy)}
    assert rates[MODEL_NAME] == {
        "model": MODEL_NAME,
        "turns": 4,
        "unreadable": 3,
        "fallbacks": 1,
        "fallback rate": 0.25,
        "reasons": "no-json 2, truncated 1",
    }
    assert rates["mock/nash"]["fallbacks"] == 0
    [flag] = flagged_runs(bumpy)
    assert flag["run"] == "test/seed-0" and flag["fallback rate"] == 0.125


def test_fallback_rates_not_flagged_at_or_below_one_in_ten(
    make_config, tmp_path, fake_model
):
    run_config(make_config(overrides=MODEL), tmp_path)
    assert flagged_runs(tmp_path) == []


def test_fallback_rates_in_lab_summary_and_the_report(bumpy, capsys):
    assert cli.main(["summary", str(bumpy)]) == 0
    out = capsys.readouterr().out
    assert "no-json 2, truncated 1" in out
    assert "Flagged: test/seed-0" in out
    page = build_report(bumpy)
    assert "Unreadable replies" in page and "no-json 2, truncated 1" in page
    assert "test/seed-0" in page
