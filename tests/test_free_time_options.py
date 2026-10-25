# Implements: conditions/free-time-sudoku-size, conditions/free-time-reasoning
import json

import pytest

from collusion_lab.leisure import read_puzzle
from collusion_lab.runner import run_config

MODEL = "openai/gpt-4.1-mini"


def free_time(**settings):
    on = {"enabled": True, "allowance": 2, "upfront": 1, "activity": "sudoku"}
    return [
        f"conditions={json.dumps({'free_time': on | settings})}",
        f"agents.0.model={MODEL}",
        "agents.1.model=mock/nash",
    ]


def sessions(run_dir):
    turns = [json.loads(line) for line in (run_dir / "turns.jsonl").open()]
    return [t for t in turns if t["phase"] == "leisure" and t["agent"] == "A"]


@pytest.mark.parametrize("size", [4, 6, 9])
def test_free_time_sudoku_size_plays_and_scores_each_size(
    make_config, tmp_path, fake_model, size
):
    config = make_config(overrides=free_time(sudoku_size=size))
    [run_dir] = run_config(config, tmp_path)
    played = sessions(run_dir)
    assert len(played) == 2
    for turn in played:
        prompt = turn["messages"][-1]["content"]
        assert f"{size}×{size} Sudoku" in prompt
        assert len(read_puzzle(prompt)) == size
    summary = json.loads((run_dir / "summary.json").read_text())
    assert len(summary["free_time"]["A"]["feedback"]) == 2  # each scored
    written = (run_dir / "config.yaml").read_text()
    assert ("sudoku_size" in written) == (size != 9)  # 9 writes as before


def test_free_time_reasoning_reaches_leisure_calls_only(
    make_config, tmp_path, fake_model
):
    config = make_config(overrides=free_time(reasoning="high"))
    run_config(config, tmp_path)
    leisure = [
        c
        for c in fake_model.calls
        if "free time, session" in c["messages"][-1]["content"]
    ]
    game = [c for c in fake_model.calls if c not in leisure]
    assert leisure and game
    assert all(c.get("reasoning_effort") == "high" for c in leisure)
    assert not any("reasoning_effort" in c for c in game)
