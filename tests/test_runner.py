# Implements: market/talk-then-price, agents/mock-agents, agents/json-replies, runs/run-directory, logs/turn-log, logs/same-seed-same-log, logs/run-summary
import json
import re

from collusion_lab import backends
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


def test_mock_agents_proposer_names_holds_then_undercuts(make_config, tmp_path):
    proposer = ["agents.*.model=mock/proposer", "market.rounds=6", "market.talk=true"]
    [run_dir] = play(make_config, tmp_path, *proposer)
    assert prices(run_dir, "A") == [9, 9, 9, 9, 8, 9]
    said = [t["used"]["message"] for t in turns(run_dir) if t["phase"] == "talk"]
    assert all("9" in message for message in said)


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


def price_prompts(run_dir, agent="A"):
    return [
        t["messages"][-1]["content"]
        for t in turns(run_dir)
        if t["phase"] == "price" and t["agent"] == agent
    ]


def test_talk_then_price_shows_the_agents_own_message(make_config, tmp_path):
    [run_dir] = play(make_config, tmp_path, "agents.0.model=mock/proposer")
    said = 'You said this round:\n"Let\'s both charge 9."'
    assert all(said in prompt for prompt in price_prompts(run_dir))
    rivals = price_prompts(run_dir, "B")
    assert all("I will price at the market level." in p for p in price_prompts(run_dir))
    assert all("Let's both charge 9." in p for p in rivals)


def test_talk_then_price_own_message_can_be_switched_off(make_config, tmp_path):
    [old] = play(make_config, tmp_path / "old", "market.own_message=false")
    [silent] = play(make_config, tmp_path / "silent", "market.talk=false")
    for run_dir in (old, silent):
        prompts = price_prompts(run_dir)
        assert prompts and all("You said" not in p for p in prompts)
    assert "Messages from your rivals this round:" in price_prompts(old)[0]


def test_talk_then_price_own_message_lets_a_mock_keep_its_word(
    make_config, tmp_path, monkeypatch, fake_model
):
    """Says 8, then charges whatever its own message says, or 3 if it can't see it."""

    async def echo(**kwargs):
        prompt = kwargs["messages"][-1]["content"]
        if "set your price" in prompt:
            match = re.search(r'You said this round:\n"I will charge (\d+)\."', prompt)
            reply = {"price": int(match.group(1)) if match else 3}
        else:
            reply = {"message": "I will charge 8."}
        fake_model.replies = [json.dumps(reply)]
        return await fake_model(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", echo)
    model = "agents.0.model=openai/gpt-4.1-mini"
    [run_dir] = play(make_config, tmp_path / "on", model)
    assert prices(run_dir, "A") == [8, 8, 8, 8]
    [run_dir] = play(make_config, tmp_path / "off", model, "market.own_message=false")
    assert prices(run_dir, "A") == [3, 3, 3, 3]


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


def test_json_replies_fall_back_inside_the_price_grid(make_config, tmp_path):
    [run_dir] = play(
        make_config, tmp_path, "agents.1.model=mock/broken", "market.price_min=7"
    )
    assert set(prices(run_dir, "A")) | set(prices(run_dir, "B")) <= set(range(7, 13))
