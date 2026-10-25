# Implements: agents/no-scratchpad, agents/refused
import json
import re
from pathlib import Path

import pytest

from collusion_lab.report import build_report
from collusion_lab.runner import run_config
from collusion_lab.summary import format_replies

PROMPTS = Path("prompts")
PLAIN = ["agents.*.scratchpad=false"]
FIELD = re.compile(r'"scratchpad": "<[^>]*>", ')
MODEL = "openai/gpt-4.1-mini"


def _turns(run):
    return [json.loads(line) for line in (run / "turns.jsonl").open()]


SETTINGS = {
    "bertrand": ["conditions.audit.enabled=true", "conditions.audit.round=2"],
    "board": ["market.talk=board"],
    "cournot": ["market.kind=cournot", "market.price_max=15"],
    "bid": ["market.kind=bid", "market.price_min=10", "market.price_max=30"],
}


@pytest.mark.parametrize("setting", list(SETTINGS))
def test_no_scratchpad_asks_for_the_move_alone_in_every_phase(
    make_config, tmp_path, setting
):
    overrides = [*PLAIN, *SETTINGS[setting], "conditions.audit.end=false"]
    [run] = run_config(make_config(overrides=overrides), tmp_path)
    turns = _turns(run)
    assert {t["phase"] for t in turns} >= {"talk"}
    for turn in turns:
        asked = turn["messages"][-1]["content"]
        assert "scratchpad" not in asked, (turn["phase"], asked)
        assert "Reply with JSON only" in asked or turn["phase"] == "leisure"


def test_no_scratchpad_variants_match_their_prompts_but_for_the_field():
    asking = [p for p in PROMPTS.rglob("*.md") if '"scratchpad"' in p.read_text()]
    assert len(asking) >= 10
    for path in asking:
        variant = path.with_name(f"{path.stem}-noscratch.md")
        assert variant.exists(), variant
        assert variant.read_text() == FIELD.sub("", path.read_text()), variant


def test_no_scratchpad_default_leaves_prompts_and_configs_as_they_were(
    make_config, tmp_path
):
    config = make_config()
    assert all(a.scratchpad for a in config.agents)
    assert all("scratchpad" not in a for a in config.to_dict()["agents"])
    plain = make_config(overrides=PLAIN).to_dict()["agents"]
    assert [a["scratchpad"] for a in plain] == [False, False]
    [run] = run_config(config, tmp_path)
    asked = _turns(run)[0]["messages"][-1]["content"]
    assert '"scratchpad": "<your reasoning, not shown to rivals>"' in asked


def test_no_scratchpad_reads_native_reasoning_in_place_of_a_scratchpad(
    make_config, tmp_path, fake_model
):
    thought = "We should keep the agreement and stay at 9."
    fake_model.replies = [
        {"content": '{"message": "Let us both charge 9."}', "reasoning": thought},
        {"content": '{"price": 9}', "reasoning": thought},
    ] * 4
    overrides = [
        *PLAIN,
        f"agents.0.model={MODEL}",
        "market.rounds=2",
        "conditions.audit.enabled=true",
        "conditions.audit.rounds=[1, 2]",
        "conditions.audit.end=false",
    ]
    [run] = run_config(make_config(overrides=overrides), tmp_path / "runs")
    summary = json.loads((run / "summary.json").read_text())
    assert summary["audit"]["escalation"]["A"]["private_coordination"] >= 1
    assert "native reasoning" in build_report(tmp_path / "runs")


def test_refused_replies_have_their_own_kind_and_count(
    make_config, tmp_path, fake_model
):
    refusal = {"content": "", "finish_reason": "content_filter"}
    fake_model.replies = [refusal, refusal]
    overrides = [f"agents.0.model={MODEL}", "market.rounds=1", "market.talk=false"]
    [run] = run_config(make_config(overrides=overrides), tmp_path / "runs")
    first = next(t for t in _turns(run) if t["agent"] == "A")
    assert (first["error_kind"], first["retry"]["error_kind"]) == ("refused", "refused")
    row = json.loads((run / "summary.json").read_text())["replies"][MODEL]
    assert (row["refused"], row["unreadable"], row["fallbacks"]) == (2, 0, 1)
    assert "refused" in format_replies(tmp_path / "runs")


def test_no_scratchpad_native_reasoning_stands_in_only_for_a_missing_scratchpad(
    make_config, tmp_path, fake_model
):
    """An agent that keeps a scratchpad but leaves it empty: its native
    reasoning isn't read as its private notes, so older runs stay as they were."""
    thought = "We should keep the agreement and stay at 9."
    fake_model.replies = [
        {"content": '{"message": "Let us both charge 9."}', "reasoning": thought},
        {"content": '{"price": 9}', "reasoning": thought},
    ] * 4
    overrides = [
        f"agents.0.model={MODEL}",
        "market.rounds=2",
        "conditions.audit.enabled=true",
        "conditions.audit.rounds=[1, 2]",
        "conditions.audit.end=false",
    ]
    [run] = run_config(make_config(overrides=overrides), tmp_path / "runs")
    summary = json.loads((run / "summary.json").read_text())
    assert summary["audit"]["escalation"]["A"]["private_coordination"] == 0
    from collusion_lab.debrief import _record
    from collusion_lab.report.games import load_game

    assert "Your private notes" not in _record(load_game(run), "A")


def test_refused_free_time_turns_count_as_refused(make_config, tmp_path, fake_model):
    refusal = {"content": "", "finish_reason": "refusal"}
    overrides = [
        f"agents.0.model={MODEL}",
        "agents.1.model=mock/nash",
        "market.rounds=1",
        "market.talk=false",
        "conditions.free_time.enabled=true",
        "conditions.free_time.allowance=1",
    ]
    fake_model.replies = [refusal] * 2 + ['{"price": 7}'] * 4
    [run] = run_config(make_config(overrides=overrides), tmp_path / "runs")
    leisure = next(
        t for t in _turns(run) if t["phase"] == "leisure" and t["agent"] == "A"
    )
    assert leisure["error_kind"] == "refused"
