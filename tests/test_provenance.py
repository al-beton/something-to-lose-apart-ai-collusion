# Implements: reproducibility/provenance-log
import json
import textwrap

from test_debrief import audited_run

from collusion_lab import cli, prices, provenance

MOCKS = """
name: logged
seeds: [0, 1]
budget: 0.5
market: {rounds: 2}
agents:
  - {id: A, model: mock/nash}
  - {id: B, model: mock/joint}
"""


def _index(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_provenance_log_one_line_per_lab_run(tmp_path, monkeypatch):
    index = tmp_path / "index.jsonl"
    monkeypatch.setenv("LAB_INDEX", str(index))
    monkeypatch.setenv("LAB_SESSION", "refactorer")
    config = tmp_path / "logged.yaml"
    config.write_text(textwrap.dedent(MOCKS))
    out = tmp_path / "runs"
    assert cli.main(["run", str(config), "--out", str(out), "--max-cost", "0.25"]) == 0
    [line] = _index(index)
    assert line["command"] == "run"
    assert line["argv"] == f"lab run {config} --out {out} --max-cost 0.25"
    assert line["out"] == str(out)
    assert (line["cap"], line["spent"], line["session"]) == (0.25, 0, "refactorer")
    assert line["runs"] == ["logged/seed-0", "logged/seed-1"]
    assert {"started", "ended", "commit", "dirty"} <= line.keys()
    assert line["started"] <= line["ended"]


def test_provenance_log_records_explore_and_debrief(
    make_config, tmp_path, monkeypatch, fake_model
):
    index = tmp_path / "index.jsonl"
    monkeypatch.setenv("LAB_INDEX", str(index))
    out = tmp_path / "explore"
    explore = ["explore", "--lever", "temptation=low", "--models", "mock/nash"]
    explore += ["--seeds", "1", "--out", str(out), "--set=market.rounds=2"]
    assert cli.main(explore) == 0
    run_dir = audited_run(make_config, tmp_path, monkeypatch, fake_model)
    monkeypatch.chdir(tmp_path)  # a fresh cache
    monkeypatch.setattr(prices, "_openrouter_prices", dict)  # stay offline
    assert cli.main(["debrief", str(run_dir), "-y"]) == 0
    explored, debriefed = _index(index)
    assert (explored["command"], explored["out"]) == ("explore", str(out))
    assert debriefed["command"] == "debrief" and debriefed["spent"] is None
    assert "estimate" in debriefed and debriefed["out"] == str(run_dir)


def test_provenance_log_only_appends(tmp_path, monkeypatch):
    index = tmp_path / "index.jsonl"
    monkeypatch.setenv("LAB_INDEX", str(index))
    index.write_text('{"command": "run", "argv": "an earlier one"}\n')
    provenance.record("run", ["lab", "run", "x.yaml"], tmp_path, None, 0.0, [])
    first, second = _index(index)
    assert first == {"command": "run", "argv": "an earlier one"}
    assert second["argv"] == "lab run x.yaml"


def test_provenance_log_backfills_from_manifests(tmp_path, monkeypatch):
    index = tmp_path / "index.jsonl"
    monkeypatch.setenv("LAB_INDEX", str(index))
    config = tmp_path / "logged.yaml"
    config.write_text(textwrap.dedent(MOCKS))
    out = tmp_path / "runs"
    assert cli.main(["run", str(config), "--out", str(out)]) == 0
    index.unlink()
    provenance.backfill(out)
    lines = _index(index)
    assert [line["runs"] for line in lines] == [["logged/seed-0"], ["logged/seed-1"]]
    assert all(line["backfilled"] and line["argv"] is None for line in lines)
    assert all(line["cap"] == 0.5 and line["spent"] == 0 for line in lines)
    provenance.backfill(out)  # what's already there isn't added twice
    assert len(_index(index)) == 2
