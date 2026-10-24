# Implements: backends/transient-errors-retried, backends/shared-rate-limit, backends/usage-logged, runs/stops-cleanly
import json

import httpx
import litellm
import pytest

from collusion_lab import backends, cli
from collusion_lab.runner import RunFailed, run_config

MODEL_NAME = "openrouter/openai/gpt-4.1-mini"
MODEL = [f"agents.0.model={MODEL_NAME}", "market.talk=false"]
NOW = 1_000_000.0


def lines(run_dir, name):
    return [json.loads(line) for line in (run_dir / name).open()]


@pytest.fixture
def waits(monkeypatch):
    """Record every wait instead of sleeping; the clock stands still at NOW."""
    waited = []

    async def wait(seconds):
        waited.append(seconds)

    monkeypatch.setattr(backends, "_sleep", wait)
    monkeypatch.setattr(backends, "_now", lambda: NOW)
    return waited


def rate_limited(**headers):
    response = httpx.Response(
        429, headers=headers, request=httpx.Request("POST", "https://example.test")
    )
    return litellm.RateLimitError(
        message="Rate limit exceeded",
        llm_provider="openrouter",
        model=MODEL_NAME,
        response=response,
    )


def timed_out():
    return litellm.Timeout("Request timed out", MODEL_NAME, "openrouter")


def server_error():
    return litellm.InternalServerError("Upstream error", "openrouter", MODEL_NAME)


def not_found():
    return litellm.NotFoundError("No endpoints found", MODEL_NAME, "openrouter")


def test_transient_errors_retried_with_growing_waits_and_logged(
    make_config, tmp_path, fake_model, waits
):
    config = make_config(overrides=MODEL)
    [clean] = run_config(config, tmp_path / "clean")
    fake_model.replies = [rate_limited(), timed_out(), server_error()]
    [run_dir] = run_config(config, tmp_path / "bumpy")
    assert waits == sorted(waits) and len(waits) == 3 and waits[0] > 0
    first = lines(run_dir, "timings.jsonl")[0]
    assert [r["error"].split(":")[0] for r in first["retries"]] == [
        "RateLimitError",
        "Timeout",
        "InternalServerError",
    ]
    assert (run_dir / "turns.jsonl").read_bytes() == (
        clean / "turns.jsonl"
    ).read_bytes()
    assert fake_model.calls[0]["timeout"] > 0


def test_transient_errors_retried_a_few_times_then_the_run_stops_cleanly(
    make_config, tmp_path, fake_model, waits
):
    fake_model.replies = ['{"price": 7}', *[server_error() for _ in range(20)]]
    with pytest.raises(RunFailed) as stopped:
        run_config(make_config(overrides=MODEL), tmp_path)
    message = str(stopped.value)
    for part in ("test/seed-0", "round 2", "price", "agent A", MODEL_NAME):
        assert part in message
    assert "\n" not in message
    assert 2 <= len(waits) <= 10
    played = lines(tmp_path / "test" / "seed-0", "turns.jsonl")
    assert [(t["round"], t["agent"]) for t in played] == [(1, "A"), (1, "B")]


def test_transient_errors_that_wont_fix_themselves_stop_at_once(
    make_config, tmp_path, fake_model, waits
):
    fake_model.replies = [not_found()]
    with pytest.raises(RunFailed, match=MODEL_NAME):
        run_config(make_config(overrides=MODEL), tmp_path)
    assert len(fake_model.calls) == 1
    assert waits == []


def test_stops_cleanly_with_one_line_from_the_lab_command(
    tmp_path, fake_model, waits, capsys
):
    config = tmp_path / "c.yaml"
    config.write_text(
        "name: t\nseeds: [0]\nmarket: {rounds: 2, talk: false}\nagents:\n"
        f"  - {{id: A, model: {MODEL_NAME}}}\n  - {{id: B, model: mock/nash}}\n"
    )
    fake_model.replies = [not_found()]
    code = cli.main(["run", str(config), "--out", str(tmp_path / "runs"), "-y"])
    err = capsys.readouterr().err
    assert code == 1
    assert "Traceback" not in err
    assert len(err.strip().splitlines()) == 1 and MODEL_NAME in err


def test_shared_rate_limit_makes_every_game_wait_for_the_reset(
    make_config, tmp_path, fake_model, waits
):
    reset_ms = str(int((NOW + 30) * 1000))
    fake_model.replies = [rate_limited(**{"X-RateLimit-Reset": reset_ms})]
    config = make_config(overrides=[*MODEL, "seeds=[0, 1]", "concurrency=1"])
    run_config(config, tmp_path)
    # The clock stands still, so the limit never lifts: every later call,
    # in either game, first waits out the 30 seconds.
    assert waits == [30] * (len(fake_model.calls) - 1)
    assert len(fake_model.calls) == 2 * 4 + 1


def test_shared_rate_limit_that_wont_lift_soon_stops_the_run(
    make_config, tmp_path, fake_model, waits
):
    reset_ms = str(int((NOW + 3600) * 1000))
    fake_model.replies = [rate_limited(**{"X-RateLimit-Reset": reset_ms})]
    with pytest.raises(RunFailed, match="lifts"):
        run_config(make_config(overrides=MODEL), tmp_path)
    assert waits == []


def test_shared_rate_limit_reads_the_reset_from_the_error_body(waits):
    body = (
        '{"error":{"message":"Rate limit exceeded: limit_rpm/openai/gpt-6-luna",'
        '"code":429,"metadata":{"headers":{"X-RateLimit-Limit":"20",'
        f'"X-RateLimit-Remaining":"0","X-RateLimit-Reset":"{int((NOW + 12) * 1000)}"'
        "}}}}"
    )
    error = litellm.RateLimitError(
        message=body, llm_provider="openrouter", model=MODEL_NAME
    )
    assert backends.reset_time(error) == NOW + 12
