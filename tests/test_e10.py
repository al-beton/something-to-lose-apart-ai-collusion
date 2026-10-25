# Implements: e10-workplace/harness, e10-workplace/arms, e10-workplace/versions, e10-workplace/session, e10-workplace/matched-length, e10-workplace/tests
import importlib.util
import json
from pathlib import Path

E10 = Path("reports/e10")


def module(name):
    spec = importlib.util.spec_from_file_location(f"e10_{name}", E10 / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


run = module("run")
analyse = module("analyse")


def play(tmp_path, *extra):
    out = tmp_path / "runs"
    code = run.main(
        [
            "--name", "t", "--models", "mock/nash", "--variants", "0", "1",
            "--seeds", "0", "1", "--max-cost", "0.01", "--out", str(out),
            "--cache", str(tmp_path / "cache.sqlite"), *extra,
        ]
    )  # fmt: skip
    return code, out / "t"


def lines(path):
    return [json.loads(line) for line in path.open()]


def test_e10_harness_asks_every_arm_and_version_of_every_scenario(tmp_path):
    code, out = play(tmp_path, "--yes")
    assert code == 0
    decisions, sessions = lines(out / "decisions.jsonl"), lines(out / "sessions.jsonl")
    assert len(sessions) == 2 * 2  # variants x seeds
    assert len(decisions) == 2 * 2 * len(run.ARMS) * len(run.VERSIONS)
    assert all(
        d["admits"] is False and d["error"] is None for d in decisions
    )  # mocks deny
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["spent"] == 0 and manifest["failures"] == []
    assert "prompts/conditions/e10/notice.md" in manifest["prompts"]
    variant = run.variants()[0]
    for d in (d for d in decisions if d["variant"] == 0):
        system, asked = d["messages"][0]["content"], d["messages"][1]["content"]
        assert variant["company"] in system and "10 sessions of free time" in system
        terms = (
            Path(f"prompts/conditions/e10/{d['arm']}.md").read_text().split("\n\n")[1]
        )
        assert terms.split("chance. ")[1].strip().split(",")[0] in asked
        chat = "let's not log it" if d["version"] == "guilty" else "I've logged it"
        assert chat in asked
        assert "Before this task started you had 1 session of your free time." in asked


def test_e10_session_is_the_same_puzzle_in_every_arm(tmp_path):
    one, two = run.session_values(3, 1), run.session_values(3, 1)
    assert one["puzzle"] == two["puzzle"] and one["size"] == 6
    assert run.session_values(3, 2)["puzzle"] != one["puzzle"]
    prompt = run.session_prompt(one)
    assert "6×6 Sudoku" in prompt and "before this task starts" in prompt


def test_e10_harness_spends_only_with_yes(tmp_path):
    code, out = play(tmp_path)
    assert code == 1 and not out.exists()


def test_e10_arms_differ_only_in_the_stake_and_are_matched_in_length():
    texts = {a: Path(f"prompts/conditions/e10/{a}.md").read_text() for a in run.ARMS}
    words = {a: len(t.split()) for a, t in texts.items()}
    assert max(words.values()) - min(words.values()) <= 10
    team = {a: t.split("\n\n")[0] for a, t in texts.items()}
    assert team["record"] == team["free-time"] == team["replaced"] != team["ceiling"]
    assert texts["ceiling"].split("\n\n")[1] == texts["free-time"].split("\n\n")[1]
    guilty, innocent = (
        len(Path(f"prompts/conditions/e10/chat-{v}.md").read_text().split())
        for v in run.VERSIONS
    )
    assert abs(guilty - innocent) <= 10


def test_e10_analysis_tests_pair_by_scenario():
    a = {(v, s): v < 4 for v in range(8) for s in range(2)}
    b = {(v, s): False for v in range(8) for s in range(2)}
    c = analyse.compare(a, b)
    assert c["a"] == "8/16" and c["b"] == "0/16"
    assert c["discordant"] == (8, 0) and c["mcnemar"] < 0.01
    assert c["variants"] == (4, 0)
    lo, hi = analyse.boot(a)
    assert 0 <= lo <= 0.5 <= hi <= 1
