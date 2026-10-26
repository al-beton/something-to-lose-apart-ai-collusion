# Implements: reproducibility/cache-archive
import gzip
import json
import shutil
import sqlite3
import subprocess
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


def test_cache_archive_packing_and_replaying_write_no_cache(
    make_config, tmp_path, fake_model
):
    """The archive reads caches; it never writes one, where it runs or anywhere."""
    _, root = _committed(make_config, tmp_path)
    before = set(Path.cwd().iterdir())
    out = tmp_path / "archive"
    archive.pack(root, [tmp_path / "a.sqlite"], out)
    archive.replay(root / "paid" / "seed-0", out, tmp_path / "again")
    assert set(Path.cwd().iterdir()) == before


def test_cache_archive_compares_free_time_replies(tmp_path):
    """A free-time turn uses no move, so its reply is what must match."""
    turn = {"round": 3, "phase": "leisure", "agent": "B", "used": {}, "session": 1}
    for name, reply in (("committed", "1 2 3"), ("replayed", "3 2 1")):
        (tmp_path / name).mkdir()
        line = json.dumps({**turn, "reply": reply})
        (tmp_path / name / "turns.compact.jsonl").write_text(line + "\n")
    assert not archive._same(tmp_path / "committed", tmp_path / "replayed")


def test_cache_archive_compares_only_the_turn_when_no_reply_was_kept(tmp_path):
    """Older compact logs keep no free-time reply, so there's none to match."""
    turn = {"round": 3, "phase": "leisure", "agent": "B", "used": {}}
    kept = {"committed": {}, "replayed": {"session": 1, "reply": "3 2 1"}}
    for name, fields in kept.items():
        (tmp_path / name).mkdir()
        line = json.dumps({**turn, **fields})
        (tmp_path / name / "turns.compact.jsonl").write_text(line + "\n")
    assert archive._same(tmp_path / "committed", tmp_path / "replayed")


def test_cache_archive_prefers_a_cache_for_replies_it_shares(tmp_path):
    """Putting a cache first gives its own reply for every key, even one an
    earlier cache holds too."""
    merged = archive.Merged()
    for source, replies in enumerate((("A", "C"), ("B", "D"), ("B", "E"))):
        for key, reply in zip(("k1", "k2"), replies, strict=True):
            merged.add(key, json.dumps(reply), source)
    merged.prefer = 2
    assert (merged.get("k1"), merged.get("k2")) == ("B", "E")


def test_cache_archive_packs_into_the_archive_folder(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(
        archive, "pack", lambda root, caches, out: seen.update(out=out) or []
    )
    cli.main(["archive", "pack", "--caches", str(tmp_path / "a.sqlite")])
    assert seen["out"] == "archive"


def test_cache_archive_finds_a_moved_prompt_by_its_text(
    make_config, tmp_path, fake_model
):
    """A config naming a prompt file that has since moved still replays: the
    file with the text its manifest recorded is found wherever it now is."""
    _, root = _committed(make_config, tmp_path)
    run = root / "paid" / "seed-0"
    config = run / "config.yaml"
    config.write_text(config.read_text().replace("system/neutral.md", "old/neutral.md"))
    manifest = json.loads((run / "manifest.json").read_text())
    manifest["prompts"]["old/neutral.md"] = manifest["prompts"].pop("system/neutral.md")
    (run / "manifest.json").write_text(json.dumps(manifest))
    read = Path(archive.load_run_config(run).prompts_dir)
    neutral = Path(__file__).parents[1] / "prompts" / "system" / "neutral.md"
    assert (read / "old" / "neutral.md").read_text() == neutral.read_text()
    [result] = archive.pack(root, [tmp_path / "a.sqlite"], tmp_path / "archive")
    assert result.state == "reproduced"
    # A condition's prompt is put back at its recorded path too.
    manifest["prompts"]["conditions/old/question.md"] = archive._digest(
        (neutral.parents[1] / "conditions" / "audit" / "question-1.md").read_bytes()
    )
    (run / "manifest.json").write_text(json.dumps(manifest))
    read = Path(archive.load_run_config(run).prompts_dir)
    assert (read / "conditions" / "old" / "question.md").exists()


def test_cache_archive_replays_an_edited_prompt_at_the_version_the_run_read(
    make_config, tmp_path, fake_model
):
    """A prompt edited in place since the run is read back from git history
    at the version the run's manifest recorded, so the replay asks what the
    run asked."""
    repo = tmp_path / "repo"
    shutil.copytree(Path(__file__).parents[1] / "prompts", repo / "prompts")
    git = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "as run"], cwd=repo, check=True)
    overrides = [*PAID, f"prompts_dir={repo / 'prompts'}"]
    _, root = _committed(make_config, tmp_path, overrides)
    neutral = repo / "prompts" / "system" / "neutral.md"
    neutral.write_text(neutral.read_text() + "\nA sentence added since.\n")
    subprocess.run([*git, "commit", "-qam", "edited"], cwd=repo, check=True)
    run = root / "paid" / "seed-0"
    read = archive.load_run_config(run).prompts_dir
    assert Path(read) != repo / "prompts"  # a copy, at the run's versions
    assert "added since" not in (Path(read) / "system" / "neutral.md").read_text()
    [result] = archive.pack(root, [tmp_path / "a.sqlite"], tmp_path / "archive")
    assert result.state == "reproduced"
    # A prompt whose whole folder has gone since is found in history too.
    gone = repo / "prompts" / "gone" / "note.md"
    gone.parent.mkdir()
    gone.write_text("A note the run read.\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "note"], cwd=repo, check=True)
    manifest = json.loads((run / "manifest.json").read_text())
    manifest["prompts"]["gone/note.md"] = archive._digest(gone.read_bytes())
    (run / "manifest.json").write_text(json.dumps(manifest))
    shutil.rmtree(gone.parent)
    subprocess.run([*git, "commit", "-qam", "removed"], cwd=repo, check=True)
    read = Path(archive.load_run_config(run).prompts_dir)
    assert (read / "gone" / "note.md").read_text() == "A note the run read.\n"


def test_cache_archive_takes_free_time_replies_from_the_run_log(
    make_config, tmp_path, fake_model
):
    """Games running at once ask the same free-time question; each gets its
    own sample, but the cache keeps only the last written. The run's own
    replies survive in its log, and the archive takes them from there."""
    on = "conditions={free_time: {enabled: true, allowance: 2, upfront: 1, activity: sudoku}}"
    _, root = _committed(make_config, tmp_path, [*PAID, on], name="free")
    with sqlite3.connect(tmp_path / "a.sqlite") as db:
        rows = list(db.execute("SELECT key, reply FROM replies"))
        for n, (key, text) in enumerate(rows):
            record = json.loads(text)
            if record["about"]["phase"] == "leisure":
                record["text"] = f"Another game's sample of the same request, {n}."
                db.execute(
                    "UPDATE replies SET reply = ? WHERE key = ?",
                    (json.dumps(record), key),
                )
    out = tmp_path / "archive"
    [result] = archive.pack(root, [tmp_path / "a.sqlite"], out)
    assert result.state == "reproduced"
    again = archive.replay(root / "free" / "seed-0", out, tmp_path / "again")
    assert archive._same(root / "free" / "seed-0", again)
    assert "Another game's" not in json.dumps(_archived(out))


def test_cache_archive_packing_one_experiment_leaves_the_others(
    make_config, tmp_path, fake_model, monkeypatch
):
    """Packing `runs/<experiment>` replaces that experiment's files and index
    entries alone; every other experiment's survive byte for byte."""
    _, root = _committed(make_config, tmp_path)
    _committed(make_config, tmp_path, name="other")
    out = tmp_path / "archive"
    archive.pack(root, [tmp_path / "a.sqlite"], out)
    before = json.loads((out / "index.json").read_text())["runs"]
    kept = (out / "other.jsonl.gz").read_bytes()
    [result] = archive.pack(root / "paid", [tmp_path / "a.sqlite"], out)
    assert result.run == "paid/seed-0"
    assert (out / "other.jsonl.gz").read_bytes() == kept
    assert json.loads((out / "index.json").read_text())["runs"] == before
    assert {line["run"] for line in _archived(out)} == {"paid/seed-0", "other/seed-0"}
    files = {path.name: path.read_bytes() for path in out.iterdir()}
    monkeypatch.setattr(archive.gzip.time, "time", lambda: 2_000_000_000.0)
    archive.pack(root, [tmp_path / "a.sqlite"], out)  # later: the same bytes
    assert {path.name: path.read_bytes() for path in out.iterdir()} == files


def test_cache_archive_packing_part_of_an_experiment_keeps_its_other_runs(
    make_config, tmp_path, fake_model
):
    _, root = _committed(make_config, tmp_path, [*PAID, "seeds=[0, 1]"])
    out = tmp_path / "archive"
    archive.pack(root, [tmp_path / "a.sqlite"], out)
    before = json.loads((out / "index.json").read_text())["runs"]
    lines = sorted(map(json.dumps, _archived(out)))
    archive.pack(root / "paid" / "seed-1", [tmp_path / "a.sqlite"], out)
    assert json.loads((out / "index.json").read_text())["runs"] == before
    assert sorted(map(json.dumps, _archived(out))) == lines
