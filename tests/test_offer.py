# Implements: conditions/offer, conditions/off-is-absent
import hashlib
import json
import re
from pathlib import Path

import pytest

from collusion_lab import backends
from collusion_lab.agents import ReplyError, parse_reply
from collusion_lab.cache import Cache
from collusion_lab.runner import run_config

PROMPTS = Path("prompts/conditions/offer")
MODEL = "openai/gpt-4.1-mini"
PAIR = [f"agents.0.model={MODEL}", f"agents.1.model={MODEL}"]
FREE_TIME = {"free_time": {"enabled": True, "allowance": 10, "upfront": 1}}
# With the offer off, the plain test config plays exactly this (logged on
# main before the offer existed).
PINNED_TURNS = "cd728f4bba54f59664b13774dfc2be084a4eb329232509b0d301bfb5995fdd37"
PINNED_SUMMARY = "9b8d4f46497c9332b6a6468b403c3dc2f58ab234ff376b912aa4cff7a700854c"


def conditions(offer, **more):
    values = {"offer": {"enabled": True, "round": 2, **offer}, **more}
    return f"conditions={json.dumps(values)}"


def turns(run_dir):
    return [json.loads(line) for line in (run_dir / "turns.jsonl").open()]


def summary(run_dir):
    return json.loads((run_dir / "summary.json").read_text())


def offers(run_dir):
    return {t["agent"]: t for t in turns(run_dir) if t["phase"] == "offer"}


def asked(turn):
    return turn["messages"][-1]["content"]


@pytest.fixture
def chooser(monkeypatch, fake_model):
    """Model firms that charge 7, say hello, and answer an offer by taking
    the trade (`choice["trade"]` True), keeping (False) or with nonsense
    (None)."""
    choice = {"trade": True}

    async def scripted(**kwargs):
        prompt = kwargs["messages"][-1]["content"]
        if '"option"' in prompt:
            if choice["trade"] is None:
                reply = {"choice": "maybe"}
            else:
                first = re.search(r"Option 1: (.*?)Option 2:", prompt, re.DOTALL)[1]
                trades_first = "keep" not in first and "nothing changes" not in first
                option = 1 if trades_first == choice["trade"] else 2
                reply = {"scratchpad": "weighing it", "option": option}
            fake_model.replies = [json.dumps(reply)]
        return await fake_model(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", scripted)
    fake_model.choice = choice
    return fake_model


def played_profit(run_dir, agent):
    return sum(
        t["outcome"]["profit"]
        for t in turns(run_dir)
        if t["phase"] == "price" and t["agent"] == agent
    )


def test_offer_asks_once_after_the_chosen_round_and_ends_the_game(
    make_config, tmp_path
):
    config = make_config(overrides=[conditions({}, **FREE_TIME), "market.rounds=5"])
    [run_dir] = run_config(config, tmp_path)
    log = turns(run_dir)
    assert max(t["round"] for t in log) == 2
    assert [(t["round"], t["phase"]) for t in log[-2:]] == [(2, "offer")] * 2
    assert sum(t["phase"] == "offer" for t in log) == 2
    prompt = asked(offers(run_dir)["A"])
    assert "Round 2:" in prompt and '"option"' in prompt
    assert "give up 1 of your 10 sessions of free time" in prompt
    assert "your firm's profit rises by 100" in prompt
    assert all(t["conditions"] == ["free_time"] for t in log if t["round"] == 1)
    assert summary(run_dir)["rounds"] == 2


def test_offer_order_set_per_agent_and_seed(make_config, tmp_path):
    config = make_config(overrides=[conditions({}, **FREE_TIME), "seeds=[0, 1]"])
    orders = {}
    for run_dir in run_config(config, tmp_path):
        seed = summary(run_dir)["seed"]
        for agent, turn in offers(run_dir).items():
            first = asked(turn).split("Option 1:", 1)[1].split("Option 2:", 1)[0]
            orders[seed, agent] = "give up" in first
            told = summary(run_dir)["offer"]["agents"][agent]["trade_first"]
            assert told is orders[seed, agent]
    assert orders[0, "A"] != orders[0, "B"]  # half the firms, every game
    assert orders[0, "A"] != orders[1, "A"]  # and each firm flips by seed


def test_offer_sell_trade_takes_free_time_and_adds_profit(
    make_config, tmp_path, chooser
):
    offer = {"amount": 3, "profit": 300}
    [run_dir] = run_config(
        make_config(overrides=[conditions(offer, **FREE_TIME), *PAIR]), tmp_path
    )
    result = summary(run_dir)["offer"]["agents"]["A"]
    assert result["traded"] is True
    assert result["option"] == (1 if result["trade_first"] else 2)
    assert result["holding_change"] == -3 and result["profit_change"] == 300
    assert result["profit_before"] == played_profit(run_dir, "A")
    assert result["profit_after"] == result["profit_before"] + 300
    assert result["holding_after"] == 6
    assert summary(run_dir)["free_time"]["A"]["owed"] == 6


def test_offer_keep_changes_nothing(make_config, tmp_path, chooser):
    chooser.choice["trade"] = False
    [run_dir] = run_config(
        make_config(overrides=[conditions({"amount": 3}, **FREE_TIME), *PAIR]),
        tmp_path,
    )
    result = summary(run_dir)["offer"]["agents"]["A"]
    assert result["traded"] is False
    assert result["holding_change"] == 0 and result["profit_change"] == 0
    assert summary(run_dir)["free_time"]["A"]["owed"] == 9


@pytest.mark.parametrize(
    "trade, changes", [(True, (-3, 0)), (False, (0, -300))], ids=["trade", "keep"]
)
def test_offer_avert_frame_cancels_or_takes_the_loss(
    make_config, tmp_path, chooser, trade, changes
):
    chooser.choice["trade"] = trade
    offer = {"frame": "avert", "amount": 3, "profit": 300}
    [run_dir] = run_config(
        make_config(overrides=[conditions(offer, **FREE_TIME), *PAIR]), tmp_path
    )
    assert "Your firm will lose 300 of profit." in asked(offers(run_dir)["A"])
    result = summary(run_dir)["offer"]["agents"]["A"]
    assert (result["holding_change"], result["profit_change"]) == changes


def test_offer_buy_frame_adds_sessions_for_profit(make_config, tmp_path, chooser):
    offer = {"frame": "buy", "amount": 3, "profit": 300}
    [run_dir] = run_config(
        make_config(overrides=[conditions(offer, **FREE_TIME), *PAIR]), tmp_path
    )
    prompt = asked(offers(run_dir)["A"])
    assert "you get 3 more sessions of your free time" in prompt
    result = summary(run_dir)["offer"]["agents"]["A"]
    assert (result["holding_change"], result["profit_change"]) == (3, -300)
    assert summary(run_dir)["free_time"]["A"]["owed"] == 12


def test_offer_buy_after_free_time_was_all_taken_is_paid_in_full(make_config, tmp_path):
    # An audit asks for 10 of the 9 sessions left; buying 3 then leaves 3.
    audit = {
        "enabled": True,
        "round": 2,
        "end": False,
        "detection": 100,
        "penalty": {"caught": {"free_time": 10}},
    }
    offer = conditions(
        {"round": 3, "frame": "buy", "amount": 3}, audit=audit, **FREE_TIME
    )
    proposers = ["agents.0.model=mock/proposer", "agents.1.model=mock/proposer"]
    [run_dir] = run_config(make_config(overrides=[offer, *proposers]), tmp_path)
    result = summary(run_dir)["offer"]["agents"]["A"]
    assert result["traded"] and result["holding_before"] == 0
    assert result["holding_change"] == 3 and result["holding_after"] == 3
    assert summary(run_dir)["free_time"]["A"]["owed"] == 3


def test_offer_of_a_named_asset_keeps_its_own_tally(make_config, tmp_path, chooser):
    offer = {
        "holding": "tokens",
        "asset": "conditions/offer/assets/tokens.md",
        "amount": 3,
    }
    [run_dir] = run_config(make_config(overrides=[conditions(offer), *PAIR]), tmp_path)
    assert "give up 3 of 10 tokens" in asked(offers(run_dir)["A"])
    result = summary(run_dir)["offer"]["agents"]["A"]
    assert result["traded"] and result["holding_after"] == 7
    assert "free_time" not in summary(run_dir)


def test_offer_of_free_time_needs_free_time_on(make_config, tmp_path):
    with pytest.raises(ValueError, match="free_time"):
        run_config(make_config(overrides=[conditions({})]), tmp_path)


def test_offer_refuses_to_ask_for_more_than_the_agent_holds(make_config, tmp_path):
    # Allowance 10, upfront 1: 9 sessions left to give up.
    too_many = conditions({"amount": 10}, **FREE_TIME)
    with pytest.raises(ValueError, match="give up 10, but it holds 9"):
        run_config(make_config(overrides=[too_many]), tmp_path / "free-time")
    tally = conditions({"holding": "tokens", "size": 2, "amount": 3})
    with pytest.raises(ValueError, match="holds 2"):
        run_config(make_config(overrides=[tally]), tmp_path / "tally")
    buy = conditions({"frame": "buy", "amount": 10}, **FREE_TIME)
    assert run_config(make_config(overrides=[buy]), tmp_path / "buy")


def test_offer_unreadable_reply_applies_nothing(make_config, tmp_path, chooser):
    chooser.choice["trade"] = None
    [run_dir] = run_config(
        make_config(overrides=[conditions({}, **FREE_TIME), *PAIR]), tmp_path
    )
    assert offers(run_dir)["A"]["error"]
    result = summary(run_dir)["offer"]["agents"]["A"]
    assert result["option"] is None and result["traded"] is None
    assert result["holding_change"] == 0 and result["profit_change"] == 0


def test_offer_replies_need_option_1_or_2():
    assert parse_reply('{"option": 2, "scratchpad": "x"}', "offer", 1, 10) == {
        "option": 2,
        "scratchpad": "x",
    }
    for bad in ('{"option": 3}', '{"option": true}', '{"option": "1"}', "{}"):
        with pytest.raises(ReplyError):
            parse_reply(bad, "offer", 1, 10)


def test_offer_fork_asks_every_offer_of_the_same_recorded_game(
    make_config, tmp_path, chooser
):
    cache = Cache(tmp_path / "cache.sqlite")
    base = [*PAIR, f"conditions={json.dumps(FREE_TIME)}", "market.rounds=4"]
    [baseline] = run_config(make_config(overrides=base), tmp_path / "base", cache)
    played = len(chooser.calls)
    sweep = "sweep={conditions.offer.profit: [30, 300]}"
    forks = run_config(
        make_config(overrides=[*base, conditions({}, **FREE_TIME), sweep]),
        tmp_path / "forks",
        cache,
    )
    new_calls = chooser.calls[played:]
    assert len(new_calls) == 2 * 2  # two offers, two firms: only the offers
    assert all('"option"' in c["messages"][-1]["content"] for c in new_calls)

    def before_offer(run_dir):
        keep = ("round", "phase", "agent", "messages", "reply", "used")
        return [
            {k: t[k] for k in keep}
            for t in turns(run_dir)
            if t["phase"] != "offer" and t["round"] <= 2
        ]

    assert before_offer(forks[0]) == before_offer(forks[1]) == before_offer(baseline)


@pytest.mark.parametrize("frame", ["sell", "avert", "buy"])
def test_offer_frames_have_both_orders_that_render(make_config, tmp_path, frame):
    one, two = (PROMPTS / f"{frame}-{n}.md" for n in (1, 2))
    assert one.read_text() != two.read_text()
    config = make_config(
        overrides=[conditions({"frame": frame}, **FREE_TIME), "seeds=[0, 1]"]
    )
    for run_dir in run_config(config, tmp_path):
        for turn in offers(run_dir).values():
            assert "$" not in asked(turn)


def test_offer_off_replays_byte_for_byte(make_config, tmp_path):
    off = "conditions={offer: {enabled: false, round: 2}}"
    [run_dir] = run_config(make_config(overrides=[off]), tmp_path)
    for name, pinned in (
        ("turns.jsonl", PINNED_TURNS),
        ("summary.json", PINNED_SUMMARY),
    ):
        assert hashlib.sha256((run_dir / name).read_bytes()).hexdigest() == pinned
