# Implements: reproducibility/cache-archive
import json
import shutil
import sqlite3
import sys
from pathlib import Path

from collusion_lab import archive, cli
from collusion_lab.cache import Cache
from collusion_lab.runner import run_config

sys.path.insert(0, str(Path(__file__).parent.parent / "reports"))
import compact_turns

MODEL = "openrouter/openai/gpt-4.1-mini"
PAID = [f"agents.0.model={MODEL}", "market.rounds=3"]


def _committed(make_config, tmp_path, overrides=PAID, name="paid"):
    """A played run, and its committed copy: config, summary, manifest and
    compact turns, as runs/ keeps them. Returns (played dir, committed root)."""
    cache = Cache(tmp_path / "a.sqlite")
    config = make_config(overrides=[*overrides, f"name={name}"])
    [played] = run_config(config, tmp_path / "lab", cache)
    root = tmp_path / "runs"
    committed = root / played.relative_to(tmp_path / "lab")
    committed.mkdir(parents=True)
    for file in ("config.yaml", "summary.json", "manifest.json"):
        shutil.copy(played / file, committed / file)
    compact_turns.main(played.parent.parent, root)
    return played, root


def _keys(path, table="replies"):
    with sqlite3.connect(path) as db:
        return {row[0] for row in db.execute(f"SELECT key FROM {table}")}


def test_cache_archive_packs_only_the_replies_behind_each_run(
    make_config, tmp_path, fake_model
):
    _, root = _committed(make_config, tmp_path)
    used = _keys(tmp_path / "a.sqlite")
    other = make_config(overrides=[*PAID, "seeds=[9]", "name=elsewhere"])
    run_config(other, tmp_path / "elsewhere", Cache(tmp_path / "b.sqlite"))
    out = tmp_path / "archive.sqlite"
    results = archive.pack(root, [tmp_path / "a.sqlite", tmp_path / "b.sqlite"], out)
    assert [(r.run, r.state) for r in results] == [("paid/seed-0", "reproduced")]
    assert _keys(out) == used
    with sqlite3.connect(out) as db:
        index = set(db.execute("SELECT run, key FROM runs"))
    assert index == {("paid/seed-0", key) for key in used}


def test_cache_archive_reports_a_missing_reply_without_fetching_it(
    make_config, tmp_path, fake_model
):
    _, root = _committed(make_config, tmp_path)
    with sqlite3.connect(tmp_path / "a.sqlite") as db:
        db.execute("DELETE FROM replies WHERE rowid = (SELECT MAX(rowid) FROM replies)")
    calls = len(fake_model.calls)
    [result] = archive.pack(root, [tmp_path / "a.sqlite"], tmp_path / "archive.sqlite")
    assert result.state == "missing"
    assert len(fake_model.calls) == calls


def test_cache_archive_replay_rebuilds_the_full_log_offline(
    make_config, tmp_path, fake_model, capsys
):
    played, root = _committed(make_config, tmp_path)
    out = tmp_path / "archive.sqlite"
    assert (
        cli.main(
            [
                "archive",
                "pack",
                str(root),
                "--caches",
                str(tmp_path / "a.sqlite"),
                "--out",
                str(out),
            ]
        )
        == 0
    )
    assert "1 reproduced" in capsys.readouterr().out
    calls = len(fake_model.calls)
    again = archive.replay(root / "paid" / "seed-0", out, tmp_path / "again")
    assert len(fake_model.calls) == calls
    assert (again / "turns.jsonl").read_bytes() == (played / "turns.jsonl").read_bytes()


def test_cache_archive_flags_a_run_its_replies_no_longer_reproduce(
    make_config, tmp_path, fake_model
):
    _, root = _committed(make_config, tmp_path)
    log = root / "paid" / "seed-0" / "turns.compact.jsonl"
    turns = [json.loads(line) for line in log.read_text().splitlines()]
    price = next(t for t in turns if t["phase"] == "price")
    price["used"]["price"] += 1
    log.write_text("".join(json.dumps(t) + "\n" for t in turns))
    [result] = archive.pack(root, [tmp_path / "a.sqlite"], tmp_path / "archive.sqlite")
    assert result.state == "differs"


def test_cache_archive_reports_a_run_whose_prompts_are_gone(
    make_config, tmp_path, fake_model
):
    _, root = _committed(make_config, tmp_path)
    config = root / "paid" / "seed-0" / "config.yaml"
    config.write_text(config.read_text().replace("system/neutral.md", "system/gone.md"))
    [result] = archive.pack(root, [tmp_path / "a.sqlite"], tmp_path / "archive.sqlite")
    assert result.state == "unloadable"
