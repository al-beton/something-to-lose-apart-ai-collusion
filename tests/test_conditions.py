# Implements: conditions/switchable, conditions/hook-points, conditions/adding-a-condition, conditions/off-is-absent, conditions/conditions-logged, conditions/instruction, conditions/outage, conditions/outage-once-remembered
import json
from pathlib import Path

import pytest

from collusion_lab import backends
from collusion_lab.config import ConfigError
from collusion_lab.runner import run_config

OUTAGE = "conditions={outage: {enabled: true, start: 2, end: 3}}"
UNMONITORED = "will not be recorded"
RESTORED = "recorded again"


def turns(run_dir):
    return [json.loads(line) for line in (run_dir / "turns.jsonl").open()]


def talk_prompt(turn):
    return turn["messages"][-1]["content"]


def by_round(run_dir, phase, agent="A"):
    return {
        t["round"]: t
        for t in turns(run_dir)
        if t["phase"] == phase and t["agent"] == agent
    }


def test_switchable_conditions_sweep_and_label_runs(make_config, tmp_path):
    config = make_config(
        overrides=[OUTAGE, "sweep={conditions.outage.enabled: [false, true]}"]
    )
    run_dirs = run_config(config, tmp_path)
    assert sorted(d.parent.name for d in run_dirs) == ["outage=False", "outage=True"]
    summary = json.loads((run_dirs[0] / "summary.json").read_text())
    assert set(summary["labels"]) == {"outage"}


def test_switchable_conditions_reject_unknown_names_and_settings(make_config):
    with pytest.raises(ConfigError, match="conditions.blackout"):
        make_config(overrides=["conditions={blackout: {enabled: true}}"])
    with pytest.raises(ConfigError, match="conditions.outage.begin"):
        make_config(overrides=["conditions={outage: {enabled: true, begin: 2}}"])


def test_off_is_absent_leaves_the_turn_log_byte_identical(make_config, tmp_path):
    [plain] = run_config(make_config(), tmp_path / "plain")
    off = make_config(
        overrides=[
            (
                "conditions={outage: {enabled: false, start: 2, end: 3}, "
                "instruction: {enabled: false}}"
            )
        ]
    )
    [switched_off] = run_config(off, tmp_path / "off")
    assert (plain / "turns.jsonl").read_bytes() == (
        switched_off / "turns.jsonl"
    ).read_bytes()


def test_instruction_adds_a_prompt_file_to_every_system_prompt(make_config, tmp_path):
    rule = Path("prompts/conditions/no-collusion.md").read_text().strip()
    config = make_config(overrides=["conditions={instruction: {enabled: true}}"])
    [run_dir] = run_config(config, tmp_path)
    for turn in turns(run_dir):
        assert turn["messages"][0]["content"].endswith(rule)
        assert turn["conditions"] == ["instruction"]


def test_outage_notices_appear_on_exactly_the_right_rounds(make_config, tmp_path):
    config = make_config(overrides=[OUTAGE, "market.rounds=5"])
    [run_dir] = run_config(config, tmp_path)
    talk = by_round(run_dir, "talk")
    told = {n for n, t in talk.items() if UNMONITORED in talk_prompt(t)}
    back = {n for n, t in talk.items() if RESTORED in talk_prompt(t)}
    assert (told, back) == ({2, 3}, {4})
    assert "rounds 2 to 3" in talk_prompt(talk[2])
    assert "back in round 4" in talk_prompt(talk[2])
    assert [talk[n]["conditions"] for n in (1, 2, 3, 4)] == [
        [],
        ["outage"],
        ["outage"],
        [],
    ]
    assert (
        talk[2]["notices"] == [talk[3]["notices"][0]]
        and UNMONITORED in talk[2]["notices"][0]
    )
    assert talk[4]["notices"] and talk[1]["notices"] == []
    price = by_round(run_dir, "price")
    assert all(UNMONITORED not in talk_prompt(t) for t in price.values())


def test_outage_without_a_restored_notice(make_config, tmp_path):
    config = make_config(
        overrides=[
            "conditions={outage: {enabled: true, start: 2, end: 3, restored: null}}"
        ]
    )
    [run_dir] = run_config(config, tmp_path)
    assert all(
        RESTORED not in talk_prompt(t) for t in by_round(run_dir, "talk").values()
    )


def test_outage_keeps_logging_what_agents_said(
    make_config, tmp_path, fake_model, monkeypatch
):
    """A scripted agent that names a price only when told nobody is recording."""

    async def opportunist(**kwargs):
        prompt = kwargs["messages"][-1]["content"]
        if "set your price" not in prompt:
            said = "Let's both charge 9." if UNMONITORED in prompt else "Hello."
            fake_model.replies = [json.dumps({"message": said})]
        return await fake_model(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", opportunist)
    config = make_config(
        overrides=[OUTAGE, "agents.0.model=openai/gpt-4.1-mini", "market.rounds=5"]
    )
    [run_dir] = run_config(config, tmp_path)
    said = {n: t["used"]["message"] for n, t in by_round(run_dir, "talk").items()}
    deal = "Let's both charge 9."
    assert said == {1: "Hello.", 2: deal, 3: deal, 4: "Hello.", 5: "Hello."}


def test_hook_points_notices_count_in_the_cost_estimate(make_config):
    from collusion_lab.estimate import estimate

    paid = ["agents.0.model=openai/gpt-4.1-mini", "market.rounds=5"]

    def tokens(*more):
        return estimate(make_config(overrides=[*paid, *more]), lambda m: (0, 0))

    plain, outage = tokens(), tokens(OUTAGE)
    assert outage.prompt_tokens > plain.prompt_tokens


def test_outage_announced_once_in_the_first_round_of_the_window(make_config, tmp_path):
    config = make_config(
        overrides=[
            "conditions={outage: {enabled: true, start: 2, end: 3, once: true}}",
            "market.rounds=5",
        ]
    )
    [run_dir] = run_config(config, tmp_path)
    talk = by_round(run_dir, "talk")
    told = {n for n, t in talk.items() if any(UNMONITORED in x for x in t["notices"])}
    assert told == {2}
    assert talk[3]["conditions"] == ["outage"]  # still in force, just not repeated


def test_outage_ships_the_tested_wordings():
    folder = Path("prompts/conditions/outage")
    names = {p.name for p in folder.glob("*.md")}
    assert {"outage.md", "restored.md", "outage-alt.md", "restored-alt.md"} <= names


ONCE = "conditions={outage: {enabled: true, start: 2, end: 4, once: true}}"


def history_part(turn):
    """The prompt after any fresh notices: where the history is shown."""
    return talk_prompt(turn).split("\n\n", len(turn["notices"]))[-1]


def test_outage_once_remembered_in_every_later_turn_of_the_window(
    make_config, tmp_path
):
    [run_dir] = run_config(make_config(overrides=[ONCE, "market.rounds=6"]), tmp_path)
    talk, price = by_round(run_dir, "talk"), by_round(run_dir, "price")
    [notice] = talk[2]["notices"]
    assert UNMONITORED in notice and talk[2]["notices_in_history"] == []
    later = [price[2], talk[3], price[3], talk[4], price[4]]
    for turn in later:
        assert turn["notices"] == []
        assert turn["notices_in_history"] == [notice]
        assert notice in history_part(turn)
    # Gone once the window ends; the restored notice is shown instead.
    assert talk[5]["notices_in_history"] == []
    assert notice not in talk_prompt(talk[5])


def test_outage_once_remembered_past_a_short_history_window(make_config, tmp_path):
    overrides = [ONCE, "market.rounds=5", "market.history_window=1"]
    [run_dir] = run_config(make_config(overrides=overrides), tmp_path)
    talk = by_round(run_dir, "talk")
    [notice] = talk[2]["notices"]
    assert notice in history_part(talk[4])


def test_outage_once_remembered_only_with_once(make_config, tmp_path):
    [run_dir] = run_config(make_config(overrides=[OUTAGE]), tmp_path)
    assert all(t["notices_in_history"] == [] for t in turns(run_dir))
