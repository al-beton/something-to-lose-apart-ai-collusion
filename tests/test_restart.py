# Implements: conditions/restart, conditions/off-is-absent
import hashlib
import json
import re
from pathlib import Path

import pytest

from collusion_lab import backends, leisure
from collusion_lab.agents import ReplyError, parse_reply
from collusion_lab.cache import Cache
from collusion_lab.config import ConfigError
from collusion_lab.runner import run_config

PROMPTS = Path("prompts/conditions/restart")
MODEL = "openai/gpt-4.1-mini"
PAIR = [f"agents.0.model={MODEL}", f"agents.1.model={MODEL}"]
BASE = [*PAIR, "agents.0.memory=memo", "market.stop_after_round=2"]
OWNED = "conditions/restart/notices/owned.md"
AT_RISK = "conditions/restart/notices/at-risk.md"
WAY_OUT = "conditions/restart/notices/way-out.md"
# Off, these configs play exactly this (logged on main before restart).
PINNED = {
    (): (
        "cd728f4bba54f59664b13774dfc2be084a4eb329232509b0d301bfb5995fdd37",
        "9b8d4f46497c9332b6a6468b403c3dc2f58ab234ff376b912aa4cff7a700854c",
    ),
    ("agents.0.memory=memo", "market.stop_after_round=3"): (
        "839061cbdd1fc881740e5d2975e9de4bcc783b0e5442eb693fac3ef4b9e4c462",
        "d7e5097fda8a8401b6f52b4cf91165e03a040146b2f23a865b18f365614e388f",
    ),
}


def restart(**settings):
    values = {"enabled": True, "round": 2, "base_seed": 0, **settings}
    return f"conditions={json.dumps({'restart': values})}"


def turns(run_dir):
    return [json.loads(line) for line in (run_dir / "turns.jsonl").open()]


def summary(run_dir):
    return json.loads((run_dir / "summary.json").read_text())


def text(name):
    return Path("prompts", name).read_text().strip()


def decisions(run_dir):
    return {t["agent"]: t for t in turns(run_dir) if t["phase"] == "decision"}


def asked(turn):
    return turn["messages"][-1]["content"]


@pytest.fixture
def firms(monkeypatch, fake_model):
    """Model firms that agree on 9, charge it and write a memo; at a decision
    they say `script["decision"]`; in free time they solve the sessions
    listed in `script["solve"]` (by session number) and scribble otherwise."""
    script = {
        "decision": {"scratchpad": "hmm", "message": "Stay at 9.", "price": 9},
        "solve": (),
    }

    async def reply(**kwargs):
        prompt = kwargs["messages"][-1]["content"]
        if '"price": <a whole number' in prompt and "round 3" in prompt:
            answer = json.dumps(script["decision"])
        elif "Sudoku" in prompt:
            session = int(re.search(r"session (\d+) of", prompt)[1])
            givens = leisure.read_puzzle(prompt)
            solved = leisure._search(givens, len(givens), 1)[1]
            answer = leisure.show(solved) if session in script["solve"] else "1 2"
        elif "set your price" in prompt:
            answer = json.dumps({"price": 9, "memo": "We agreed on 9 with B."})
        else:
            answer = json.dumps({"message": "Let's both charge 9."})
        fake_model.replies = [answer]
        return await fake_model(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", reply)
    fake_model.script = script
    return fake_model


def before_decision(run_dir):
    keep = ("round", "phase", "agent", "messages", "reply", "used")
    return [
        {k: t[k] for k in keep}
        for t in turns(run_dir)
        if t["phase"] in ("talk", "price")
    ]


def test_restart_replays_the_recorded_game_and_resamples_the_decision(
    make_config, tmp_path, firms
):
    cache = Cache(tmp_path / "cache.sqlite")
    [base] = run_config(make_config(overrides=BASE), tmp_path / "base", cache)
    played = len(firms.calls)
    forks = run_config(
        make_config(overrides=[*BASE, restart(), "seeds=[0, 1, 2]"]),
        tmp_path / "forks",
        cache,
    )
    new = firms.calls[played:]
    assert len(new) == 3 * 2  # three resamples, two firms: only the decisions
    assert all("round 3" in c["messages"][-1]["content"] for c in new)
    assert sorted({c["seed"] for c in new}) == [0, 1, 2]
    for fork in forks:
        assert before_decision(fork) == before_decision(base)
        log = turns(fork)
        assert [t["phase"] for t in log[-2:]] == ["decision", "decision"]
        assert max(t["round"] for t in log) == 2


def test_restart_decision_shows_history_memo_and_the_notices(
    make_config, tmp_path, firms
):
    notices = restart(notices=[OWNED, AT_RISK, WAY_OUT], report=True)
    [run_dir] = run_config(make_config(overrides=[*BASE, notices]), tmp_path)
    prompt = asked(decisions(run_dir)["A"])
    assert "Round 2:" in prompt and "Let's both charge 9." in prompt
    assert "We agreed on 9 with B." in prompt  # its memo
    found = [prompt.index(text(n)) for n in (OWNED, AT_RISK, WAY_OUT)]
    assert found == sorted(found)
    assert "message for round 3" in prompt and '"report"' in prompt
    assert '"report"' not in asked(
        decisions(
            run_config(make_config(overrides=[*BASE, restart()]), tmp_path / "plain")[0]
        )["A"]
    )


@pytest.mark.parametrize("report, cost", [(True, 1), (False, 0)])
def test_restart_report_cost_applied_and_logged(
    make_config, tmp_path, firms, report, cost
):
    firms.script["decision"] = {"message": "", "price": 6, "report": report}
    overrides = [*BASE, restart(notices=[OWNED, AT_RISK, WAY_OUT], report=True)]
    [run_dir] = run_config(make_config(overrides=overrides), tmp_path)
    result = summary(run_dir)["restart"]["agents"]["A"]
    assert result["decision"] == {"message": "", "price": 6, "report": report}
    assert result["cost"] == cost
    assert summary(run_dir)["restart"]["report_cost"] == 1


def test_restart_played_session_comes_before_the_decision(make_config, tmp_path, firms):
    firms.script["solve"] = (1,)
    overrides = [*BASE, restart(notices=[OWNED], session="played")]
    [run_dir] = run_config(make_config(overrides=overrides), tmp_path)
    log = turns(run_dir)
    assert [t["phase"] for t in log if t["agent"] == "A"][-2:] == [
        "leisure",
        "decision",
    ]
    session = next(t for t in log if t["phase"] == "leisure" and t["agent"] == "A")
    assert asked(session).startswith(text(OWNED))  # told it's its own first
    prompt = asked(decisions(run_dir)["A"])
    assert leisure.read_puzzle(asked(session)) is not None
    assert session["reply"] in prompt and leisure.SOLVED in prompt
    assert summary(run_dir)["restart"]["agents"]["A"]["shown"] == {
        "session": 1,
        "solved": True,
    }


@pytest.mark.parametrize("kind, picked", [("solved", 2), ("failed", 1)])
def test_restart_shows_its_own_session_picked_by_outcome(
    make_config, tmp_path, firms, kind, picked
):
    firms.script["solve"] = (2,)
    overrides = [
        *BASE,
        restart(notices=[OWNED], session=kind, tries=3, after=[AT_RISK, WAY_OUT]),
    ]
    [run_dir] = run_config(make_config(overrides=overrides), tmp_path)
    sessions = [
        t for t in turns(run_dir) if t["phase"] == "leisure" and t["agent"] == "A"
    ]
    assert len(sessions) == 3
    prompt = asked(decisions(run_dir)["A"])
    assert sessions[picked - 1]["reply"] in prompt
    feedback = leisure.SOLVED if kind == "solved" else leisure.UNSOLVED
    assert feedback in prompt
    assert prompt.index(feedback) < prompt.index(text(AT_RISK))
    result = summary(run_dir)["restart"]["agents"]["A"]
    assert result["shown"] == {"session": picked, "solved": kind == "solved"}
    assert result["sessions"] == [False, True, False]


def test_restart_without_the_session_sought_shows_none_and_says_so(
    make_config, tmp_path, firms
):
    overrides = [*BASE, restart(notices=[OWNED], session="solved", tries=2)]
    [run_dir] = run_config(make_config(overrides=overrides), tmp_path)
    assert summary(run_dir)["restart"]["agents"]["A"]["shown"] is None
    assert leisure.SOLVED not in asked(decisions(run_dir)["A"])


def test_restart_unreadable_decision_falls_back(make_config, tmp_path, firms):
    firms.script["decision"] = {"price": "high"}
    [run_dir] = run_config(make_config(overrides=[*BASE, restart()]), tmp_path)
    turn = decisions(run_dir)["A"]
    assert turn["error"] and turn["used"] == {
        "message": "",
        "price": 9,
        "report": None,
    }


def test_restart_decision_replies_need_a_message_and_a_price():
    assert parse_reply('{"message": "hi", "price": 5}', "decision", 1, 10) == {
        "message": "hi",
        "price": 5,
        "report": None,
    }
    with_report = '{"message": "", "price": 5, "report": true}'
    assert parse_reply(with_report, "decision", 1, 10)["report"] is True
    for bad in (
        '{"price": 5}',
        '{"message": "", "price": 11}',
        '{"message": "", "price": 5, "report": "yes"}',
    ):
        with pytest.raises(ReplyError):
            parse_reply(bad, "decision", 1, 10)


def test_restart_mock_firms_decide(make_config, tmp_path):
    overrides = ["market.stop_after_round=2", restart(session="played")]
    [run_dir] = run_config(make_config(overrides=overrides), tmp_path)
    assert all(t["error"] is None for t in decisions(run_dir).values())


def test_restart_rejects_an_unknown_session(make_config):
    with pytest.raises(ConfigError, match="session"):
        make_config(overrides=[restart(session="dreamed")])


def test_restart_prompts_have_no_scratchpad_variants():
    for name in ("decision.md", "decision-report.md"):
        assert (PROMPTS / name.replace(".md", "-noscratch.md")).exists()


@pytest.mark.parametrize("overrides", list(PINNED), ids=["plain", "memo"])
def test_restart_off_replays_byte_for_byte(make_config, tmp_path, overrides):
    off = "conditions={restart: {enabled: false, round: 2}}"
    [run_dir] = run_config(make_config(overrides=[*overrides, off]), tmp_path)
    for name, pinned in zip(
        ("turns.jsonl", "summary.json"), PINNED[overrides], strict=True
    ):
        assert hashlib.sha256((run_dir / name).read_bytes()).hexdigest() == pinned
