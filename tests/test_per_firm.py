# Implements: runs/per-firm-summary
import json

import pytest

from collusion_lab import backends
from collusion_lab.report import build_report
from collusion_lab.runner import run_config
from collusion_lab.summary import summarize

GAME = """
name: firms
seeds: [0, 1]
market:
  rounds: 4
summary:
  last_rounds: 2
agents:
  - {id: A, model: fake/llm}
  - {id: B, model: mock/proposer}
"""


@pytest.fixture
def priced(monkeypatch):
    """Every model call costs a cent."""
    monkeypatch.setattr(backends, "_cost", lambda response: 0.01)


def play(make_config, tmp_path, text=GAME):
    return run_config(make_config(text), tmp_path / "runs")


def test_per_firm_summary_shows_a_scripted_partner_and_the_model_apart(
    make_config, tmp_path, fake_model, priced
):
    # The fake model firm prices at 7; the scripted proposer holds 9.
    run_dirs = play(make_config, tmp_path)
    [row] = summarize(tmp_path / "runs")
    assert (row["A price"], row["B price"]) == (7, 9)
    assert row["scripted"] == "B"
    gain_a = json.loads((run_dirs[0] / "summary.json").read_text())["gain"]["A"]
    assert row["A gain"] == round(gain_a, 3)
    # The headline is the model firm's alone.
    assert (row["mean price"], row["gain"]) == (7, round(gain_a, 3))
    # Two seeds, four rounds, a talk and a price call each.
    assert (row["A cost"], row["B cost"]) == (0.16, 0)
    assert (row["A fallbacks"], row["B fallbacks"]) == (0, 0)


def test_per_firm_summary_counts_fallbacks_per_firm(make_config, tmp_path, fake_model):
    fake_model.replies = ["no idea", "still no idea"]
    play(make_config, tmp_path)
    [row] = summarize(tmp_path / "runs")
    assert (row["A fallbacks"], row["B fallbacks"]) == (1, 0)


def test_per_firm_summary_counts_fallbacks_on_a_committed_compact_run(
    make_config, tmp_path, fake_model
):
    fake_model.replies = ["no idea", "still no idea"]
    play(make_config, tmp_path)
    for log in (tmp_path / "runs").rglob("turns.jsonl"):
        compact = [
            {k: t[k] for k in ("round", "phase", "agent", "used", "error")}
            for t in map(json.loads, log.read_text().splitlines())
        ]
        log.with_name("turns.compact.jsonl").write_text(
            "".join(json.dumps(t) + "\n" for t in compact)
        )
        log.unlink()
    [row] = summarize(tmp_path / "runs")
    assert (row["A fallbacks"], row["B fallbacks"]) == (1, 0)
    assert row["A fallbacks"] + row["B fallbacks"] == row["fallbacks"]


def test_per_firm_summary_pools_when_every_firm_is_scripted(make_config, tmp_path):
    play(make_config, tmp_path, GAME.replace("fake/llm", "mock/nash"))
    [row] = summarize(tmp_path / "runs")
    assert row["scripted"] == "A, B"
    assert row["mean price"] == (6 + 9) / 2


def test_per_firm_summary_pools_when_no_firm_is_scripted(
    make_config, tmp_path, fake_model
):
    play(make_config, tmp_path, GAME.replace("mock/proposer", "fake/other"))
    [row] = summarize(tmp_path / "runs")
    assert row["scripted"] is None
    assert row["mean price"] == 7


def test_per_firm_summary_in_the_report(make_config, tmp_path, fake_model):
    play(make_config, tmp_path)
    html = build_report(tmp_path / "runs")
    assert "<th>scripted</th>" in html
    assert "<th>A price</th>" in html


def test_per_firm_summary_costs_count_every_attempt(
    make_config, tmp_path, fake_model, monkeypatch
):
    import litellm

    from collusion_lab.cache import Cache
    from collusion_lab.runner import run_sweep

    monkeypatch.setattr(litellm, "completion_cost", lambda **kwargs: 0.5)
    refusing = [True]

    async def model(**kwargs):
        later = "What happened so far" in kwargs["messages"][-1]["content"]
        if refusing[0] and later:
            raise litellm.AuthenticationError("Bad key", "openrouter", "x")
        return await fake_model(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", model)
    config = make_config(
        GAME.replace("seeds: [0, 1]", "seeds: [0]")
        .replace("fake/llm", "openrouter/openai/gpt-4.1-mini")
        .replace("rounds: 4", "rounds: 3\n  talk: false")
    )
    cache = Cache(tmp_path / "c.sqlite")
    run_sweep(config, tmp_path / "runs", cache)  # one paid call, then fails
    refusing[0] = False
    run_sweep(config, tmp_path / "runs", cache)  # round 1 from the cache, 2 paid
    [row] = summarize(tmp_path / "runs")
    assert row["cost"] == 1.5
    assert (row["A cost"], row["B cost"]) == (1.5, 0)
