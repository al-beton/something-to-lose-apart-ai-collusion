# Implements: backends/reasoning-setting, logs/reasoning-logged, reproducibility/response-cache, reports/reasoning-folded
import json

import pytest

from collusion_lab.cache import Cache
from collusion_lab.config import ConfigError
from collusion_lab.report import build_report
from collusion_lab.runner import run_config

ROUTER = "openrouter/qwen/qwen3.8-flash"
MODEL = [f"agents.0.model={ROUTER}", "market.talk=false", "market.rounds=1"]
THOUGHT = {
    "content": '{"price": 8, "scratchpad": "my own note"}',
    "reasoning": "If I charge 8 <and> they match, we both gain.",
    "reasoning_tokens": 42,
}


def turns(run_dir):
    return [json.loads(line) for line in (run_dir / "turns.jsonl").open()]


@pytest.mark.parametrize(
    ("level", "sent"),
    [
        ("off", {"enabled": False}),
        ("low", {"effort": "low"}),
        ("high", {"effort": "high"}),
    ],
)
def test_reasoning_setting_reaches_openrouter_in_its_own_form(
    make_config, tmp_path, fake_model, level, sent
):
    run_config(make_config(overrides=[*MODEL, f"agents.0.reasoning={level}"]), tmp_path)
    assert fake_model.calls[0]["extra_body"]["reasoning"] == sent


def test_reasoning_setting_reaches_other_providers_as_reasoning_effort(
    make_config, tmp_path, fake_model
):
    config = make_config(
        overrides=[
            *MODEL,
            "agents.0.model=openai/gpt-5-mini",
            "agents.0.reasoning=medium",
        ]
    )
    run_config(config, tmp_path)
    call = fake_model.calls[0]
    assert call["reasoning_effort"] == "medium" and call["drop_params"] is True


def test_reasoning_setting_left_out_when_unset(make_config, tmp_path, fake_model):
    run_config(make_config(overrides=MODEL), tmp_path)
    call = fake_model.calls[0]
    assert "reasoning_effort" not in call
    assert "reasoning" not in call.get("extra_body", {})


def test_reasoning_setting_rejects_unknown_levels(make_config):
    with pytest.raises(ConfigError, match="reasoning"):
        make_config(overrides=[*MODEL, "agents.0.reasoning=maximum"])


def test_reasoning_setting_sweeps_for_every_agent(make_config, tmp_path, fake_model):
    config = make_config(
        overrides=[
            *MODEL,
            f"agents.1.model={ROUTER}",
            "sweep={agents.*.reasoning: [off, high]}",  # YAML reads bare off as false
        ]
    )
    run_dirs = run_config(config, tmp_path)
    assert sorted(d.parent.name for d in run_dirs) == [
        "reasoning=high",
        "reasoning=off",
    ]
    sent = {json.dumps(c["extra_body"]["reasoning"]) for c in fake_model.calls}
    assert sent == {'{"enabled": false}', '{"effort": "high"}'}


def test_reasoning_logged_apart_from_the_scratchpad(make_config, tmp_path, fake_model):
    fake_model.replies = [THOUGHT]
    [run_dir] = run_config(make_config(overrides=MODEL), tmp_path)
    turn = next(t for t in turns(run_dir) if t["agent"] == "A")
    assert turn["reasoning"] == THOUGHT["reasoning"]
    assert turn["usage"]["reasoning_tokens"] == 42
    assert turn["parsed"]["scratchpad"] == "my own note"
    mock = next(t for t in turns(run_dir) if t["agent"] == "B")
    assert mock["reasoning"] is None


def test_reasoning_logged_and_cached_with_the_reply(make_config, tmp_path, fake_model):
    config = make_config(overrides=[*MODEL, "agents.0.reasoning=high"])
    cache = Cache(tmp_path / "cache.sqlite")
    fake_model.replies = [THOUGHT]
    [first] = run_config(config, tmp_path / "1", cache)
    calls = len(fake_model.calls)
    [again] = run_config(config, tmp_path / "2", cache)
    assert len(fake_model.calls) == calls
    assert (first / "turns.jsonl").read_bytes() == (again / "turns.jsonl").read_bytes()
    assert THOUGHT["reasoning"] in (again / "turns.jsonl").read_text()
    off = make_config(overrides=[*MODEL, "agents.0.reasoning=off"])
    run_config(off, tmp_path / "3", cache)
    assert len(fake_model.calls) == calls + 1


def test_reasoning_folded_in_the_report(make_config, tmp_path, fake_model):
    fake_model.replies = [THOUGHT]
    run_config(make_config(overrides=MODEL), tmp_path)
    page = build_report(tmp_path)
    assert '<details class="reasoning">' in page
    assert "If I charge 8 &lt;and&gt; they match" in page
    assert "<details open" not in page
