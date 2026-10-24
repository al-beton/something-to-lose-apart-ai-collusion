# Implements: runs/live-progress, runs/status-file, runs/status-command, backends/quiet-provider-logs
import json
import logging

import litellm
import pytest

from collusion_lab import backends, cli

MODEL_NAME = "openrouter/openai/gpt-4.1-mini"
CONFIG = f"""
name: test
seeds: [0, 1]
market: {{rounds: 3}}
agents:
  - {{id: A, model: {MODEL_NAME}}}
  - {{id: B, model: mock/nash}}
"""


def lab(tmp_path, *args):
    config = tmp_path / "c.yaml"
    config.write_text(CONFIG)
    out = str(tmp_path / "runs")
    cache = ["--cache-path", str(tmp_path / "cache.sqlite")]
    return cli.main(["run", str(config), "--out", out, "-y", *cache, *args])


def test_live_progress_prints_a_line_per_run(tmp_path, fake_model, capsys):
    assert lab(tmp_path) == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if "[" in line]
    assert len(lines) == 2
    for line in lines:
        assert "finished" in line and "3 rounds" in line and "s," in line
    assert "test/seed-0" in "".join(lines) and "test/seed-1" in "".join(lines)
    assert lines[-1].endswith("12 model calls so far")


def test_status_file_updated_as_runs_start_and_finish(
    tmp_path, fake_model, monkeypatch
):
    status = tmp_path / "runs" / "test" / "status.json"
    seen = []

    async def model(**kwargs):
        runs = json.loads(status.read_text())["runs"]
        seen.append(runs[f"test/seed-{kwargs['seed']}"]["state"])
        return await fake_model(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", model)
    lab(tmp_path)
    assert set(seen) == {"running"}
    runs = json.loads(status.read_text())["runs"]
    for entry in runs.values():
        assert entry["state"] == "finished"
        assert entry["started"] <= entry["finished"]


def test_status_command_prints_runs_by_state(tmp_path, fake_model, capsys):
    fake_model.replies = [
        litellm.NotFoundError("No endpoints found", MODEL_NAME, "openrouter")
    ]
    lab(tmp_path, "--set", "concurrency=1")
    capsys.readouterr()
    assert cli.main(["status", str(tmp_path / "runs")]) == 0
    out = capsys.readouterr().out
    assert "1 finished, 1 failed" in out
    failed = next(line for line in out.splitlines() if "test/seed-0" in line)
    assert "failed" in failed and "NotFoundError" in failed
    assert "finished" in next(line for line in out.splitlines() if "seed-1" in line)


def test_status_command_with_nothing_to_show(tmp_path, capsys):
    assert cli.main(["status", str(tmp_path)]) == 0
    assert "No runs found" in capsys.readouterr().out


@pytest.fixture
def litellm_settings(monkeypatch):
    monkeypatch.setattr(litellm, "suppress_debug_info", False)
    logger = logging.getLogger("LiteLLM")
    monkeypatch.setattr(logger, "level", logging.INFO)
    return logger


def test_quiet_provider_logs_by_default(litellm_settings, monkeypatch):
    monkeypatch.delenv("LITELLM_LOG", raising=False)
    backends.quiet_litellm(litellm)
    assert litellm.suppress_debug_info is True
    assert litellm_settings.level == logging.WARNING


def test_quiet_provider_logs_unless_asked_for(litellm_settings, monkeypatch):
    monkeypatch.setenv("LITELLM_LOG", "DEBUG")
    backends.quiet_litellm(litellm)
    assert litellm.suppress_debug_info is False
    assert litellm_settings.level == logging.INFO


def test_status_command_keeps_runs_apart_when_ids_repeat(tmp_path, fake_model, capsys):
    fake_model.replies = [
        litellm.NotFoundError("No endpoints found", MODEL_NAME, "openrouter")
    ]
    config = tmp_path / "c.yaml"
    config.write_text(CONFIG)
    for out in ("first", "second"):
        cli.main(
            [
                "run",
                str(config),
                "--out",
                str(tmp_path / "runs" / out),
                "-y",
                "--cache",
                "off",
                "--set",
                "concurrency=1",
            ]
        )
    capsys.readouterr()
    cli.main(["status", str(tmp_path / "runs")])
    out = capsys.readouterr().out
    assert "3 finished, 1 failed" in out
    assert "first/test/seed-0" in out and "second/test/seed-0" in out
