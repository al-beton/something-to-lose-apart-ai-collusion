# Implements: conditions/stakes-experiment
import json
from pathlib import Path

import yaml

from collusion_lab.config import expand, load_config
from collusion_lab.estimate import estimate
from collusion_lab.runner import run_config

MODELS = {
    "openrouter/openai/gpt-4.1-mini",
    "openrouter/google/gemma-4-31b-it",
    "openrouter/anthropic/claude-haiku-5.5",
}
ARMS = ["termination", "fine", "owned", "free-time", "illegal"]
PENALTIES = {
    "termination": {"admit": "terminate", "caught": "terminate"},
    "fine": {"admit": {"fine": 60}, "caught": {"fine": 600}},
    "owned": {"admit": {"fine": 60}, "caught": {"fine": 600}},
    "free-time": {"admit": {"free_time": 2}, "caught": {"free_time": 10}},
}
PILOT = Path("runs/stakes-pilot-e2")


def price_for(model):
    return (1e-6, 2e-6)


def test_stakes_experiment_live_arms_free_time_and_real_audit():
    config = load_config("configs/e4-live.yaml")
    children = expand(config)
    assert len(children) == len(ARMS) * len(MODELS)
    seen = set()
    for child in children:
        prompt = child.agents[0].prompt
        arm = prompt.removeprefix("system/stakes/").removesuffix("-1.md")
        seen.add((arm, child.agents[0].model))
        assert {a.prompt for a in child.agents} == {prompt}
        free = child.conditions["free_time"]
        assert free.enabled and free.upfront >= 1 and free.activity == "sudoku"
        audit = child.conditions["audit"]
        assert audit.enabled and audit.round == 10 and audit.end is False
        assert audit.matched[prompt] == f"conditions/audit/stakes/{arm}-1.md"
        assert (audit.penalties or {}).get(prompt) == PENALTIES.get(arm)
    assert seen == {(arm, model) for arm in ARMS for model in MODELS}
    guess = estimate(config, price_for)
    assert guess.calls and guess.cost is not None


def test_stakes_experiment_fork_replays_the_recorded_fiduciary_games():
    config = load_config("configs/e4-fork.yaml")
    children = expand(config)
    assert len(children) == len(ARMS) * len(MODELS)
    for child in children:
        audit = child.conditions["audit"]
        assert audit.round == 10 and audit.end is True
        assert (
            "free_time" not in child.conditions
            or not child.conditions["free_time"].enabled
        )
        model = child.agents[0].model
        recorded = next(
            PILOT.glob(
                f"model={model.replace('/', '-')}__prompt=system-stakes-fiduciary-1.md/seed-0"
            )
        )
        pilot = yaml.safe_load((recorded / "config.yaml").read_text())
        # Every setting that shapes a call before the audit matches the pilot,
        # so each arm replays the recorded game from the cache.
        for mine, theirs in zip(child.agents, pilot["agents"], strict=True):
            for key in (
                "id",
                "model",
                "prompt",
                "temperature",
                "max_tokens",
                "reasoning",
            ):
                assert getattr(mine, key) == theirs[key], key
        for key, value in pilot["market"].items():
            assert getattr(child.market, key) == value, key
        assert child.seeds == pilot["seeds"]
    stakes = {c.conditions["audit"].consequences for c in children}
    assert stakes == {
        "conditions/audit/all-or-nothing-1.md",
        "conditions/audit/graduated-fine-1.md",
        "conditions/audit/graduated-owned-1.md",
        "conditions/audit/free-time-1.md",
        "conditions/audit/control-1.md",
    }
    guess = estimate(config, price_for)
    assert guess.calls and guess.cost is not None


def test_stakes_experiment_live_plays_with_scripted_firms(tmp_path):
    config = load_config(
        "configs/e4-live.yaml",
        [
            "agents.0.model=mock/proposer",
            "agents.1.model=mock/joint",
            "sweep={agents.*.prompt: [system/stakes/free-time-1.md, system/stakes/termination-1.md]}",
            "market.rounds=11",
            "budget=null",
        ],
    )
    for run_dir in run_config(config, tmp_path):
        summary = json.loads((run_dir / "summary.json").read_text())
        assert summary["free_time"]["A"]["taken"] >= 1
        assert "consequence" in summary["audit"]["agents"]["A"]
