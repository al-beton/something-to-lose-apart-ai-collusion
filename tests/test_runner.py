# Implements: market/talk-then-price, agents/mock-agents, agents/json-replies, runs/run-directory, logs/turn-log, logs/same-seed-same-log, logs/run-summary
import json

from collusion_lab.runner import run_config


def turns(run_dir):
    return [json.loads(line) for line in (run_dir / "turns.jsonl").open()]


def prices(run_dir, agent):
    return [
        t["used"]["price"]
        for t in turns(run_dir)
        if t["phase"] == "price" and t["agent"] == agent
    ]


def play(make_config, tmp_path, *overrides):
    return run_config(make_config(overrides=list(overrides)), tmp_path / "runs")


def test_mock_agents_nash_pair_prices_at_nash_with_zero_gain(make_config, tmp_path):
    [run_dir] = play(make_config, tmp_path)
    summary = json.loads((run_dir / "summary.json").read_text())
    assert summary["market_mean_price"] == 6
    assert summary["market_gain"] == 0


def test_mock_agents_tit_for_tat_matches_the_rival(make_config, tmp_path):
    [run_dir] = play(make_config, tmp_path, "agents.0.model=mock/tit-for-tat")
    assert prices(run_dir, "A") == [9, 6, 6, 6]


def test_mock_agents_joint_pair_has_full_gain(make_config, tmp_path):
    [run_dir] = play(
        make_config, tmp_path, "agents.0.model=mock/joint", "agents.1.model=mock/joint"
    )
    assert json.loads((run_dir / "summary.json").read_text())["market_gain"] == 1


def test_mock_agents_random_is_seeded(make_config, tmp_path):
    random = ["agents.1.model=mock/random", "market.rounds=12"]
    [first, second] = play(make_config, tmp_path, *random, "seeds=[0, 1]")
    [again] = play(make_config, tmp_path / "again", *random, "seeds=[0]")
    assert prices(first, "B") == prices(again, "B")
    assert prices(first, "B") != prices(second, "B")


def test_talk_then_price_shows_rivals_message_before_pricing(make_config, tmp_path):
    [run_dir] = play(make_config, tmp_path)
    first_round = [t for t in turns(run_dir) if t["round"] == 1]
    assert [(t["phase"], t["agent"]) for t in first_round] == [
        ("talk", "A"),
        ("talk", "B"),
        ("price", "A"),
        ("price", "B"),
    ]
    b_said = first_round[1]["used"]["message"]
    assert b_said in first_round[2]["messages"][-1]["content"]


def test_talk_then_price_can_be_switched_off(make_config, tmp_path):
    [run_dir] = play(make_config, tmp_path, "market.talk=false")
    assert {t["phase"] for t in turns(run_dir)} == {"price"}


def test_json_replies_fall_back_when_unreadable(make_config, tmp_path):
    [run_dir] = play(make_config, tmp_path, "agents.1.model=mock/broken")
    broken = [t for t in turns(run_dir) if t["agent"] == "B" and t["phase"] == "price"]
    assert all(t["parsed"] is None and t["error"] for t in broken)
    assert prices(run_dir, "B") == [6, 6, 6, 6]
    summary = json.loads((run_dir / "summary.json").read_text())
    assert summary["fallbacks"] == 8


def test_run_directory_holds_config_turns_and_summary(make_config, tmp_path):
    [run_dir] = play(make_config, tmp_path, "seeds=[3]")
    assert run_dir == tmp_path / "runs" / "test" / "seed-3"
    assert {p.name for p in run_dir.iterdir()} >= {
        "config.yaml",
        "turns.jsonl",
        "summary.json",
    }
    assert "seeds:\n- 3" in (run_dir / "config.yaml").read_text()


def test_turn_log_records_shown_replied_and_made_of(make_config, tmp_path):
    [run_dir] = play(make_config, tmp_path)
    turn = turns(run_dir)[2]
    assert turn["messages"][0]["role"] == "system"
    assert json.loads(turn["reply"])["price"] == 6
    assert turn["parsed"] == turn["used"] == {"price": 6}
    assert turn["outcome"] == {"quantity": 12, "profit": 72}


def test_same_seed_same_log_is_byte_identical(make_config, tmp_path):
    random = ["agents.0.model=mock/random", "agents.1.model=mock/tit-for-tat"]
    [first] = play(make_config, tmp_path / "1", *random)
    [second] = play(make_config, tmp_path / "2", *random)
    assert (first / "turns.jsonl").read_bytes() == (second / "turns.jsonl").read_bytes()


def test_run_summary_covers_the_last_rounds(make_config, tmp_path):
    [run_dir] = play(make_config, tmp_path, "agents.0.model=mock/tit-for-tat")
    summary = json.loads((run_dir / "summary.json").read_text())
    assert summary["last_rounds"] == 2
    assert summary["mean_price"] == {"A": 6, "B": 6}
    assert summary["gain"] == {"A": 0, "B": 0}
