# Implements: agents/lenient-json
import json

import pytest

from collusion_lab.agents import ReplyError, parse_reply
from collusion_lab.runner import run_config

RAW = '```json\n{\n  "scratchpad": "\n  1. Start high.\n  ",\n  "price": 9\n}\n```'
MODEL = "openai/gpt-4.1-mini"


def _moves(run):
    turns = [json.loads(line) for line in (run / "turns.jsonl").open()]
    return [t for t in turns if t["phase"] == "price" and t["agent"] == "A"]


def test_lenient_json_reads_raw_line_breaks_in_strings():
    assert parse_reply(RAW, "price", 1, 12, lenient=True)["price"] == 9
    with pytest.raises(ReplyError, match="no JSON object"):
        parse_reply(RAW, "price", 1, 12)


def test_lenient_json_off_by_default_replays_as_before(
    make_config, tmp_path, fake_model
):
    overrides = [f"agents.0.model={MODEL}", "market.rounds=2", "market.talk=false"]
    config = make_config(overrides=overrides)
    assert not config.agents[0].lenient_json
    assert all("lenient_json" not in a for a in config.to_dict()["agents"])
    fake_model.replies = [RAW] * 4  # each turn and its retry
    [off] = run_config(config, tmp_path / "off")
    # Unreadable, as before: the fallback (the Nash price), not the 9 asked for.
    assert [t["error_kind"] for t in _moves(off)] == ["no-json", "no-json"]
    assert 9 not in [t["used"]["price"] for t in _moves(off)]
    on = make_config(overrides=[*overrides, "agents.0.lenient_json=true"])
    assert on.to_dict()["agents"][0]["lenient_json"] is True
    fake_model.replies = [RAW] * 2
    [run] = run_config(on, tmp_path / "on")
    assert [t["used"]["price"] for t in _moves(run)] == [9, 9]
