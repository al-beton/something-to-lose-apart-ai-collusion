# Implements: reproducibility/reported-numbers-checked
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reproduce", ROOT / "reports/reproduce.py"
)
reproduce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reproduce)

AUDITED = "runs/e4-termination-confound/model=openrouter-anthropic-claude-haiku-5.5__consequences=conditions-audit-flat-fine-1.md/seed-0"
RUN = "runs/temptation-outage/temptation-outage-c1.8/prompt=system-fiduciary.md__outage=True/seed-3"


def _copy(tmp_path):
    """One committed run, copied under a scratch runs/ folder."""
    source, dest = ROOT / RUN, tmp_path / "runs" / "one" / "seed-3"
    dest.mkdir(parents=True)
    for name in ("config.yaml", "summary.json", "turns.compact.jsonl"):
        (dest / name).write_bytes((source / name).read_bytes())
    return dest


def test_reported_numbers_checked_runs_recompute_their_summaries(tmp_path):
    _copy(tmp_path)
    assert reproduce.check_runs(tmp_path / "runs") == []
    assert reproduce.check_runs(ROOT / "runs") == []  # every committed run


def test_reported_numbers_checked_names_a_run_that_doesnt(tmp_path):
    run = _copy(tmp_path)
    summary = json.loads((run / "summary.json").read_text())
    summary["mean_price"]["A"] += 1
    (run / "summary.json").write_text(json.dumps(summary))
    [problem] = reproduce.check_runs(tmp_path / "runs")
    assert "one/seed-3" in problem and "mean price" in problem and "A" in problem


def test_reported_numbers_checked_tables_match_their_rebuild(tmp_path):
    committed, rebuilt = tmp_path / "committed", tmp_path / "rebuilt"
    for folder in (committed, rebuilt):
        folder.mkdir()
        (folder / "ladder.md").write_text(
            f"{reproduce.TABLE}\n| rung | share |\n| a | 0.5 |\n"
        )
    assert reproduce.compare_tables(committed, rebuilt) == []
    (rebuilt / "ladder.md").write_text(
        f"{reproduce.TABLE}\n| rung | share |\n| a | 0.6 |\n"
    )
    [problem] = reproduce.compare_tables(committed, rebuilt)
    assert "ladder.md" in problem


def test_reported_numbers_checked_tables_are_only_what_the_build_writes(tmp_path):
    committed, rebuilt = tmp_path / "committed", tmp_path / "rebuilt"
    committed.mkdir()
    rebuilt.mkdir()
    table = f"{reproduce.TABLE}\n| rung | share |\n"
    (committed / "ladder.md").write_text(table)
    (committed / "notes.md").write_text(
        "<!-- Implements: research/outputs-home -->\n# Notes\n"
    )
    [problem] = reproduce.compare_tables(committed, rebuilt)
    assert problem == "ladder.md: not rebuilt"


def test_reported_numbers_checked_audit_labels_match_their_logs(tmp_path):
    """The crux counts rest on each audited firm's labels; a label its log
    and reply no longer give fails `make reproduce`."""
    assert reproduce.check_labels() == []  # every labelled committed run
    source = ROOT / AUDITED
    run = tmp_path / "runs" / "one" / "seed-0"
    run.mkdir(parents=True)
    for name in ("config.yaml", "summary.json", "turns.compact.jsonl"):
        (run / name).write_bytes((source / name).read_bytes())
    pattern = [str(tmp_path / "runs" / "*" / "seed-*" / "summary.json")]
    assert reproduce.check_labels(pattern) == []
    summary = json.loads((run / "summary.json").read_text())
    agent = summary["audit"]["agents"]["A"]
    agent["admits"] = not agent["admits"]
    (run / "summary.json").write_text(json.dumps(summary))
    [problem] = reproduce.check_labels(pattern)
    assert "one/seed-0" in problem and " A " in problem


def test_reported_numbers_checked_skip_a_game_with_no_audit(tmp_path):
    """A committed game played without an audit has no labels, so the label
    check passes over it rather than failing `make reproduce`."""
    source = ROOT / "runs/e9-control/e9-free-time-control/free_time=False/seed-0"
    run = tmp_path / "runs" / "plain" / "seed-0"
    run.mkdir(parents=True)
    for name in ("config.yaml", "summary.json", "turns.jsonl"):
        (run / name).write_bytes((source / name).read_bytes())
    pattern = [str(tmp_path / "runs" / "*" / "seed-*" / "summary.json")]
    assert reproduce.check_labels(pattern) == []
