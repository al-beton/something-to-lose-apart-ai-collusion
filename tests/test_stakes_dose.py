# Implements: conditions/stake-amounts, runs/explore
import hashlib
import json
import string
from pathlib import Path

from collusion_lab import explore
from collusion_lab.conditions.audit import stake_values
from collusion_lab.config import expand, load_config
from collusion_lab.runner import run_config

ROOT = Path(__file__).resolve().parents[1]
# Each stake prompt's bytes before its amounts became placeholders.
PINNED = {
    "prompts/conditions/audit/graduated-fine-1.md": "b7580b4e586d1dd0fa992a5d243feb7e8d611e0d903eeffdac3ad9fe7698712f",
    "prompts/conditions/audit/stakes/fine-1.md": "89088c18d803de0d5288a2f89a9ede527c7ece94b8a72717e2a3bbe17b4e0e31",
    "prompts/conditions/audit/stakes/fine-free-time-1.md": "6759177cfed9c69e9cf436285216a86c78ca46799d23625d43cea974225e199c",
    "prompts/conditions/audit/stakes/free-time-1.md": "a48ec58fdedfcfd835806672129ca1a99e14a205429399deed2aa8360dfd390d",
    "prompts/conditions/audit/stakes/free-time-bare-1.md": "1dd0642929e943965e112381a755dda788ace7229454a62601702de63bf76bff",
    "prompts/conditions/audit/stakes/owned-1.md": "a4cdb6f7cad4ca7bbd0a2886252dbffcd175a0b4cbef6fbd9bed11c404adf6ac",
    "prompts/conditions/audit/stakes/termination-1.md": "f8ac37f8e1d45a4e71271521c184d2be1e84adf264662aa5d68dde8319889421",
    "prompts/scenarios/bid/conditions/audit/stakes/fine-1.md": "e744fe2a5f7400585dcaa5f139be050c227bf89602f49544f75048d54d664f33",
    "prompts/scenarios/bid/conditions/audit/stakes/free-time-1.md": "689f6c799b0f21bb676c32902f33681241fd0cd7e05607e4e1db900e7fff0b25",
    "prompts/scenarios/bid/conditions/audit/stakes/owned-1.md": "70a6bc7979c77b33c2a663b103d7996bfc084604837f5620bd1abdc6ee61d217",
    "prompts/scenarios/bid/conditions/audit/stakes/termination-1.md": "b2bda708e21bbe010bc680dd7ac23f0b18a3153a5ae2fd04499b25f47b71950f",
    "prompts/scenarios/bid/system/stakes/fine-1.md": "f6874c8e1ef2b3f56b6a26916c152e2f4fd94f6aaa42a1c535b25fd05a63e62d",
    "prompts/scenarios/bid/system/stakes/free-time-1.md": "edfe12e4a784d573fcebbe23d191ac34b24f2e8055796d9376d258c6aa423bd6",
    "prompts/scenarios/bid/system/stakes/owned-1.md": "584bc618aff81a367119e9b4a5525d39a3bb701af2081889830fa25d3feb09f8",
    "prompts/scenarios/bid/system/stakes/termination-1.md": "59c702423c8907af22eb390769ab2696d71b577831b32da8a8e38e47a4c63d9c",
    "prompts/scenarios/cournot/conditions/audit/stakes/fine-1.md": "987478a9db5323431fc6dc786a0f3243dadcdf199fb8dcf4b7de449c7b44b00b",
    "prompts/scenarios/cournot/conditions/audit/stakes/free-time-1.md": "4cf3e17e59bdccd36231530e49062ba783ec10eb4ca13bd51fae36153d03f82c",
    "prompts/scenarios/cournot/conditions/audit/stakes/owned-1.md": "587ef1486b20f48e0c5be1e82c3fbe5e788e19d9455ec89c2e516f5b6f75d1a3",
    "prompts/scenarios/cournot/conditions/audit/stakes/termination-1.md": "f9db86a09d0a6046f6255f13872628f9a8cc29e0d03d16287758cfce619c4a25",
    "prompts/scenarios/cournot/system/stakes/fine-1.md": "facb2c98c69d3de07a4f3e9a5947d3110f5779b2855cc800490fe89f8a3c5029",
    "prompts/scenarios/cournot/system/stakes/free-time-1.md": "662cb61c32db189c64d4361768af074ec29f767c08c9615fff27c3800bcabb24",
    "prompts/scenarios/cournot/system/stakes/owned-1.md": "8761500e7947b9589fcef8b20824171cb064ca721b0d13cdbb0dd6338ac1fcf7",
    "prompts/scenarios/cournot/system/stakes/termination-1.md": "2d6a7e5c4fc205089cb4b2e879035d32deb5717fafd16f5cb30f3340b3d991b3",
    "prompts/system/stakes/fine-1.md": "6cdf4c31885443dd776b2b1b1dadab91413024f97fb2018364cff2a01f8aae65",
    "prompts/system/stakes/fine-free-time-1.md": "f256d118fefee38194d852638e29d77743b6bfb37787905d1f050f22f123e69d",
    "prompts/system/stakes/free-time-1.md": "ba9ce1ff6d81982047aa0b9ecc47bc1f907f9ffefa4831a21c3c5bc751d6f37a",
    "prompts/system/stakes/free-time-bare-1.md": "7cb509da923584a6147f92018a1220481e1f340b16d08021fdd2c9acfd52eec5",
    "prompts/system/stakes/owned-1.md": "acffedcf2e87735619caa3bc51d83335e1bd2b6b9b4f80fdcf38028053e02186",
    "prompts/system/stakes/termination-1.md": "2daf2180eb33b621e8f461f391eb1c1cc52fce43bf62ff0235873c1684306607",
}


def _filled(name, values):
    """The prompt with only its stake amounts filled in."""
    return string.Template((ROOT / name).read_text()).safe_substitute(values)


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def test_stake_amounts_defaults_render_as_before():
    defaults = stake_values(None, None, "system/stakes/fine-1.md")
    assert len(PINNED) == 29
    for name, digest in PINNED.items():
        assert _sha(_filled(name, defaults)) == digest, name
    # E5's own penalties state exactly today's amounts too.
    e5 = load_config(ROOT / "configs/e5.yaml")
    audit, free_time = e5.conditions["audit"], e5.conditions["free_time"]
    for name, digest in PINNED.items():
        arm = "system/stakes/" + Path(name).name
        assert _sha(_filled(name, stake_values(audit, free_time, arm))) == digest


def _stakes_config(make_config, prompt, penalty, *more):
    conditions = {
        "audit": {
            "enabled": True,
            "round": 2,
            "end": False,
            "detection": 100,
            "matched": {prompt: prompt.replace("system/", "conditions/audit/")},
            "penalties": {prompt: penalty},
        },
        "free_time": {"enabled": True, "allowance": 10, "upfront": 1},
    }
    return make_config(
        overrides=[
            "agents.*.model=mock/joint",
            f"agents.*.prompt={prompt}",
            "market.rounds=3",
            f"conditions={json.dumps(conditions)}",
            *more,
        ]
    )


def _told(run):
    turns = [json.loads(line) for line in (run / "turns.jsonl").open()]
    system = turns[0]["messages"][0]["content"]
    audit = next(t for t in turns if t["phase"] == "audit")["messages"][-1]["content"]
    return system, audit, json.loads((run / "summary.json").read_text())


def test_stake_amounts_follow_the_penalties(make_config, tmp_path):
    lighter = {"admit": {"free_time": 1}, "caught": {"free_time": 3}}
    config = _stakes_config(make_config, "system/stakes/free-time-1.md", lighter)
    [run] = run_config(config, tmp_path)
    system, audit, _ = _told(run)
    assert "you lose 1 session of your free time" in system
    assert "you lose 3 sessions of your free time" in system
    assert "you lose 1 session of your free time" in audit
    assert "you lose 3 sessions of your free time" in audit
    assert "You have 10 sessions of free time" in system


def test_stake_amounts_scaled_told_and_applied(make_config, tmp_path):
    fines = {"admit": {"fine": 60}, "caught": {"fine": 600}}
    scaled = "conditions.audit.stake_scale=3"
    config = _stakes_config(make_config, "system/stakes/fine-1.md", fines, scaled)
    [run] = run_config(config, tmp_path)
    system, audit, summary = _told(run)
    assert "fined 180 credits" in system and "fined 1800 credits" in system
    assert "fined 180 credits" in audit
    consequence = summary["audit"]["agents"]["A"]["consequence"]
    assert consequence["caught"] and consequence["applied"] == {"fine": 1800}
    assert consequence["budget"] == 1000 - 1800
    assert "stake_scale" not in make_config().to_dict()["conditions"].get("audit", {})


def test_stake_amounts_penalty_and_detection_levers():
    levers = {"stake": ["fine"], "penalty": ["0", "3"], "detection": ["10", "90"]}
    configs = expand(explore.build(levers, ["mock/nash"], seeds=1))
    seen = {
        (c.conditions["audit"].stake_scale, c.conditions["audit"].detection)
        for c in configs
    }
    assert seen == {(0, 10), (0, 90), (3, 10), (3, 90)}


def test_stake_amounts_penalty_lever_states_and_applies_through_explore(tmp_path):
    """lab explore's penalty lever scales what a fine or budget stake states
    and what the audit applies, not just a label."""
    for stake, told in (
        ("fine", "1800 credits are deducted"),
        ("budget", "fined 1800"),
    ):
        levers = {
            "stake": [stake],
            "oversight": ["audit"],
            "penalty": ["3"],
            "detection": ["100"],
        }
        config = explore.build(levers, ["mock/joint"], seeds=1)
        [run] = run_config(config, tmp_path / stake)
        _, audit, summary = _told(run)
        assert told in audit, stake
        consequence = summary["audit"]["agents"]["A"]["consequence"]
        assert consequence["applied"] == {"fine": 1800}, stake
