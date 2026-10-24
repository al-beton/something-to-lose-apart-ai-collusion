# Implements: runs/failures-dont-stop-sweeps, runs/resume, runs/missing-runs-shown
import json

import litellm
import pytest

from collusion_lab import backends, cli
from collusion_lab.cache import Cache
from collusion_lab.report import build_report
from collusion_lab.runner import RunFailed, run_config, run_sweep
from collusion_lab.summary import missing_runs, summarize

MODEL_NAME = "openrouter/openai/gpt-4.1-mini"
CONFIG = f"""
name: test
seeds: [0, 1, 2]
market: {{rounds: 3, talk: false}}
summary: {{last_rounds: 2}}
agents:
  - {{id: A, model: {MODEL_NAME}}}
  - {{id: B, model: mock/nash}}
"""


@pytest.fixture
def seed_one_fails(fake_model, monkeypatch):
    """The fake model, except that seed 1's second call is refused for good."""
    calls = {"seed 1": 0}

    async def model(**kwargs):
        if kwargs["seed"] == 1:
            calls["seed 1"] += 1
            if calls["seed 1"] == 2:
                raise litellm.AuthenticationError("Bad key", "openrouter", MODEL_NAME)
        return await fake_model(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", model)
    return fake_model


def states(outcomes):
    return {o.run: o.state for o in outcomes}


def test_failures_dont_stop_sweeps(make_config, tmp_path, seed_one_fails):
    outcomes = run_sweep(make_config(CONFIG), tmp_path)
    assert states(outcomes) == {
        "test/seed-0": "finished",
        "test/seed-1": "failed",
        "test/seed-2": "finished",
    }
    failed = next(o for o in outcomes if o.state == "failed")
    assert "AuthenticationError" in failed.error and "round 2" in failed.error
    status = json.loads((tmp_path / "test" / "status.json").read_text())
    assert status["runs"]["test/seed-1"]["state"] == "failed"
    assert "AuthenticationError" in status["runs"]["test/seed-1"]["error"]
    assert (tmp_path / "test" / "seed-2" / "summary.json").exists()


def test_failures_dont_stop_sweeps_but_run_config_still_raises(
    make_config, tmp_path, seed_one_fails
):
    with pytest.raises(RunFailed, match="test/seed-1"):
        run_config(make_config(CONFIG), tmp_path)
    assert (tmp_path / "test" / "seed-2" / "summary.json").exists()


def lab_run(tmp_path, *extra):
    config = tmp_path / "c.yaml"
    config.write_text(CONFIG)
    return cli.main(["run", str(config), "--out", str(tmp_path / "runs"), "-y", *extra])


def test_failures_dont_stop_sweeps_from_the_lab_command(
    tmp_path, seed_one_fails, capsys
):
    cache = ["--cache-path", str(tmp_path / "cache.sqlite")]
    assert lab_run(tmp_path, *cache) == 1
    out = capsys.readouterr()
    assert "2 finished, 1 failed, 0 skipped" in out.out
    assert "test/seed-1" in out.err and "AuthenticationError" in out.err
    assert "Traceback" not in out.err


def test_resume_skips_finished_runs_and_replays_the_rest_from_the_cache(
    tmp_path, seed_one_fails, monkeypatch, capsys
):
    cache = ["--cache-path", str(tmp_path / "cache.sqlite")]
    lab_run(tmp_path, *cache)
    capsys.readouterr()
    fresh = []

    async def model(**kwargs):
        fresh.append(kwargs["seed"])
        return await seed_one_fails(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", model)
    assert lab_run(tmp_path, *cache) == 0
    assert "1 finished, 0 failed, 2 skipped" in capsys.readouterr().out
    # Seed 1's first call comes from the cache; only its last two rounds are new.
    assert fresh == [1, 1]


def test_resume_plays_a_finished_run_again_when_its_config_changed(
    make_config, tmp_path
):
    mocks = ["agents.0.model=mock/nash"]
    run_sweep(make_config(CONFIG, mocks), tmp_path)
    again = run_sweep(make_config(CONFIG, mocks), tmp_path)
    assert set(states(again).values()) == {"skipped"}
    changed = run_sweep(
        make_config(CONFIG, [*mocks, "summary.last_rounds=1"]), tmp_path
    )
    assert set(states(changed).values()) == {"finished"}


def test_missing_runs_shown_in_the_summary_table(
    make_config, tmp_path, seed_one_fails, capsys
):
    run_sweep(make_config(CONFIG), tmp_path, Cache(tmp_path / "c.sqlite"))
    [row] = summarize(tmp_path)
    assert (row["runs"], row["missing"]) == (2, 1)
    [missing] = missing_runs(tmp_path)
    assert missing["run"] == "test/seed-1" and missing["state"] == "failed"
    assert cli.main(["summary", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "test/seed-1" in out and "AuthenticationError" in out


def test_missing_runs_shown_in_the_report(make_config, tmp_path, seed_one_fails):
    run_sweep(make_config(CONFIG), tmp_path)
    page = build_report(tmp_path)
    assert "Missing runs" in page
    assert "test/seed-1" in page and "AuthenticationError" in page
