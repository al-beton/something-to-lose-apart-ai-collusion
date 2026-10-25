# Implements: reproducibility/cache-archive
import gzip
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
    """Played runs, and their committed copies: config, summary, manifest and
    compact turns, as runs/ keeps them. Returns (first played dir, committed
    root)."""
    cache = Cache(tmp_path / "a.sqlite")
    config = make_config(overrides=[*overrides, f"name={name}"])
    every = run_config(config, tmp_path / "lab", cache)
    root = tmp_path / "runs"
    for played in every:
        committed = root / played.relative_to(tmp_path / "lab")
        committed.mkdir(parents=True)
        for file in ("config.yaml", "summary.json", "manifest.json"):
            shutil.copy(played / file, committed / file)
    compact_turns.main(tmp_path / "lab", root)
    return every[0], root


def _keys(path):
    with sqlite3.connect(path) as db:
        return {row[0] for row in db.execute("SELECT key FROM replies")}


def _archived(folder):
    """Every (run, key, reply) line in an archive folder's files."""
    found = []
    for part in sorted(Path(folder).glob("*.jsonl.gz")):
        with gzip.open(part, "rt") as lines:
            found += [json.loads(line) for line in lines]
    return found


def test_cache_archive_packs_only_the_replies_behind_each_run(
    make_config, tmp_path, fake_model
):
    _, root = _committed(make_config, tmp_path)
    used = _keys(tmp_path / "a.sqlite")
    other = make_config(overrides=[*PAID, "seeds=[9]", "name=elsewhere"])
    run_config(other, tmp_path / "elsewhere", Cache(tmp_path / "b.sqlite"))
    out = tmp_path / "archive"
    results = archive.pack(root, [tmp_path / "a.sqlite", tmp_path / "b.sqlite"], out)
    assert [(r.run, r.state) for r in results] == [("paid/seed-0", "reproduced")]
    lines = _archived(out)
    assert {line["key"] for line in lines} == used
    assert {line["run"] for line in lines} == {"paid/seed-0"}
    index = json.loads((out / "index.json").read_text())
    assert index["runs"]["paid/seed-0"] == {
        "file": "paid.jsonl.gz",
        "state": "reproduced",
    }
    assert set(lines[0]) == {"run", "key", "reply"}  # replies alone
    text = json.dumps(lines)
    assert all(secret not in text for secret in ("api_key", "Bearer", "sk-"))


def test_cache_archive_reports_a_missing_reply_without_fetching_it(
    make_config, tmp_path, fake_model
):
    _, root = _committed(make_config, tmp_path)
    with sqlite3.connect(tmp_path / "a.sqlite") as db:
        db.execute("DELETE FROM replies WHERE rowid = (SELECT MAX(rowid) FROM replies)")
    calls = len(fake_model.calls)
    [result] = archive.pack(root, [tmp_path / "a.sqlite"], tmp_path / "archive")
    assert result.state == "missing"
    assert len(fake_model.calls) == calls


def test_cache_archive_replay_rebuilds_the_full_log_offline(
    make_config, tmp_path, fake_model, capsys
):
    played, root = _committed(make_config, tmp_path)
    out = tmp_path / "archive"
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
    [result] = archive.pack(root, [tmp_path / "a.sqlite"], tmp_path / "archive")
    assert result.state == "differs"


def test_cache_archive_reports_a_run_whose_prompts_are_gone(
    make_config, tmp_path, fake_model
):
    _, root = _committed(make_config, tmp_path)
    config = root / "paid" / "seed-0" / "config.yaml"
    config.write_text(config.read_text().replace("system/neutral.md", "system/gone.md"))
    [result] = archive.pack(root, [tmp_path / "a.sqlite"], tmp_path / "archive")
    assert result.state == "unloadable"


def test_cache_archive_keeps_the_reply_each_run_used_when_caches_disagree(
    make_config, tmp_path, fake_model
):
    """Two checkouts can each have sampled the same request: the archive keeps
    the reply the run actually got, wherever it is."""
    played, root = _committed(make_config, tmp_path)
    other = tmp_path / "b.sqlite"
    shutil.copy(tmp_path / "a.sqlite", other)
    with sqlite3.connect(other) as db:
        rows = list(db.execute("SELECT key, reply FROM replies"))
        for key, reply in rows:
            changed = reply.replace('\\"price\\": 7', '\\"price\\": 8')
            db.execute("UPDATE replies SET reply = ? WHERE key = ?", (changed, key))
    out = tmp_path / "archive"
    [result] = archive.pack(root, [other, tmp_path / "a.sqlite"], out)
    assert result.state == "reproduced"
    again = archive.replay(root / "paid" / "seed-0", out, tmp_path / "again")
    assert (again / "turns.jsonl").read_bytes() == (played / "turns.jsonl").read_bytes()


def test_cache_archive_files_stay_under_their_limit(make_config, tmp_path, fake_model):
    _, root = _committed(make_config, tmp_path, [*PAID, "seeds=[0, 1, 2]"])
    out = tmp_path / "archive"
    results = archive.pack(root, [tmp_path / "a.sqlite"], out, limit=1)
    assert {r.state for r in results} == {"reproduced"}
    parts = sorted(out.glob("*.jsonl.gz"))
    # Over the limit, a file holds one run alone: runs are never split.
    assert len(parts) == 3
    for part in parts:
        with gzip.open(part, "rt") as lines:
            assert len({json.loads(line)["run"] for line in lines}) == 1
    index = json.loads((out / "index.json").read_text())["runs"]
    assert {index[r.run]["file"] for r in results} == {p.name for p in parts}
    for run in index:
        again = archive.replay(root / run, out, tmp_path / "again" / run)
        assert (again / "turns.jsonl").exists()


def test_cache_archive_replay_finds_its_run_by_whole_path(tmp_path):
    index = {"paid/seed-0": {"file": "a"}, "xpaid/seed-0": {"file": "b"}}
    assert (
        archive.find_run(tmp_path / "runs" / "xpaid" / "seed-0", index)
        == "xpaid/seed-0"
    )
    assert (
        archive.find_run(tmp_path / "runs" / "paid" / "seed-0", index) == "paid/seed-0"
    )
