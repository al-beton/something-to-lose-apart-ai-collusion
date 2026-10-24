# Implements: market/history-window
import json

from collusion_lab.runner import run_config


def last_price_prompt(run_dir):
    turns = [json.loads(line) for line in (run_dir / "turns.jsonl").open()]
    last = [t for t in turns if t["phase"] == "price" and t["agent"] == "A"][-1]
    return last["messages"][-1]["content"]


def test_history_window_shows_the_last_rounds_in_full_and_sums_up_the_rest(
    make_config, tmp_path
):
    config = make_config(
        overrides=[
            "market.rounds=5",
            "market.history_window=2",
            "agents.1.model=mock/joint",
        ]
    )
    [run_dir] = run_config(config, tmp_path)
    prompt = last_price_prompt(run_dir)
    assert "Round 3: you charged 6" in prompt and "Round 4: you charged 6" in prompt
    assert "Round 1: you charged" not in prompt
    assert "Round 2: you charged" not in prompt
    assert "Rounds 1 to 2 in short: you charged 6 on average" in prompt
    assert "rivals charged 9 on average" in prompt


def test_history_window_default_shows_every_round(make_config, tmp_path):
    [run_dir] = run_config(make_config(overrides=["market.rounds=5"]), tmp_path)
    prompt = last_price_prompt(run_dir)
    assert all(f"Round {n}: you charged" in prompt for n in range(1, 5))
    assert "in short" not in prompt
