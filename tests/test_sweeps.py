# Implements: runs/sweeps, runs/parallel, runs/summary-table, backends/spend-asks-first
import asyncio
import json
from types import SimpleNamespace

import pytest

from collusion_lab import backends, cli
from collusion_lab.config import ConfigError
from collusion_lab.runner import paid_calls, run_config
from collusion_lab.summary import format_table, summarize

SWEEP = """
name: grid
seeds: [0, 1, 2]
market: {rounds: 3, talk: false}
summary: {last_rounds: 2}
agents:
  - {id: A, model: mock/nash}
  - {id: B, model: mock/nash}
sweep:
  agents.*.model: [mock/nash, mock/joint]
  market.rounds: [2, 3]
"""


def summaries(run_dirs):
    return [json.loads((d / "summary.json").read_text()) for d in run_dirs]


def test_sweeps_play_every_combination_for_every_seed(make_config, tmp_path):
    run_dirs = run_config(make_config(SWEEP), tmp_path)
    assert len(run_dirs) == 12 == len(set(run_dirs))
    assert tmp_path / "grid" / "model=mock-joint__rounds=3" / "seed-2" in run_dirs
    labels = {json.dumps(s["labels"], sort_keys=True) for s in summaries(run_dirs)}
    assert len(labels) == 4


def test_sweeps_set_one_value_for_every_agent(make_config, tmp_path):
    run_dirs = run_config(make_config(SWEEP), tmp_path)
    joint = [s for s in summaries(run_dirs) if s["labels"]["model"] == "mock/joint"]
    assert all(s["market_gain"] == 1 for s in joint)


def test_parallel_runs_stay_within_the_limit(make_config, tmp_path, monkeypatch):
    active = {"now": 0, "most": 0}

    async def slow_model(**kwargs):
        active["now"] += 1
        active["most"] = max(active["most"], active["now"])
        await asyncio.sleep(0.01)
        active["now"] -= 1
        reply = SimpleNamespace(content='{"price": 7}')
        return SimpleNamespace(choices=[SimpleNamespace(message=reply)], model="m")

    monkeypatch.setattr(backends, "_acompletion", slow_model)
    config = make_config(
        overrides=[
            "agents.0.model=openai/gpt-4.1-mini",
            "market.talk=false",
            "market.rounds=1",
            "seeds=[0, 1, 2, 3, 4, 5]",
            "concurrency=2",
        ]
    )
    run_config(config, tmp_path)
    assert active["most"] == 2


def test_summary_table_groups_by_the_swept_values(make_config, tmp_path):
    run_config(make_config(SWEEP), tmp_path)
    rows = summarize(tmp_path / "grid")
    assert len(rows) == 4
    assert {r["runs"] for r in rows} == {3}
    joint = next(r for r in rows if r["model"] == "mock/joint" and r["rounds"] == 3)
    assert (joint["mean price"], joint["gain"], joint["fallbacks"]) == (9, 1, 0)
    table = format_table(rows)
    assert table.splitlines()[0].startswith("| model | rounds | runs | mean price |")


def test_summary_table_groups_by_any_config_value(make_config, tmp_path):
    run_config(make_config(SWEEP), tmp_path)
    rows = summarize(tmp_path / "grid", by=["market.rounds"])
    assert [(r["market.rounds"], r["runs"]) for r in rows] == [(2, 6), (3, 6)]


def test_summary_table_from_the_lab_command(make_config, tmp_path, capsys):
    run_config(make_config(SWEEP), tmp_path)
    assert cli.main(["summary", str(tmp_path / "grid")]) == 0
    assert "| model | rounds |" in capsys.readouterr().out


def test_spend_asks_first_counts_every_sweep_run(make_config):
    config = make_config(SWEEP.replace("mock/joint]", "openai/gpt-4.1-mini]"))
    assert paid_calls(config) == 3 * (2 + 3) * 2


def test_sweeps_give_every_combination_its_own_directory(make_config, tmp_path):
    sweep = SWEEP.replace(
        "  agents.*.model: [mock/nash, mock/joint]\n  market.rounds: [2, 3]\n",
        "  agents.*.api_base: [http://localhost:8000/v1, http://localhost:8000-v1]\n",
    )
    run_dirs = run_config(make_config(sweep), tmp_path)
    assert len(run_dirs) == 6 == len(set(run_dirs))


def test_parallel_needs_a_limit_of_at_least_one(make_config):
    with pytest.raises(ConfigError, match="concurrency"):
        make_config(overrides=["concurrency=0"])


def test_summary_table_groups_by_list_values(make_config, tmp_path):
    sweep = SWEEP.replace(
        "  agents.*.model: [mock/nash, mock/joint]\n  market.rounds: [2, 3]\n",
        "  seeds: [[0, 1], [2]]\n",
    )
    run_config(make_config(sweep), tmp_path)
    rows = summarize(tmp_path / "grid")
    assert [(r["seeds"], r["runs"]) for r in rows] == [("[0, 1]", 2), ("[2]", 1)]
    assert len(summarize(tmp_path / "grid", by=["agents.*.model"])) == 1
