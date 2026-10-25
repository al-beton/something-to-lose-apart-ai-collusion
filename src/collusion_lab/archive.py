# Implements: reproducibility/cache-archive
"""One archive of the cached replies behind every committed run, and offline
replay from it.

Replies live in response caches (see cache.py), one per checkout, so nobody
else can replay our runs from them. `pack(root, caches, out)` merges the
caches it is given and replays every committed run under `root` (each folder
with a `config.yaml`) against them, offline: a call the caches can't answer
fails the run rather than reaching a model. The replies each replay read are
written to `out`, an SQLite file: `replies (id, key, reply)` and `runs (run,
key, reply)`, the index from each run to the reply it read for each key.
Caches in different checkouts each sampled their own replies, so one request
can have several; a run that the first cache's replies don't reproduce is
replayed again with each disagreeing cache put first, and the archive keeps
the replies of the attempt that reproduced it.

Each run ends in one state:
- `reproduced`: every reply was there, and the replay made the same move
  and message, turn for turn, as the run's committed log;
- `differs`: every reply was there, but the replay's decisions differ (a
  prompt file edited since the run changes what is asked, so its replies
  answer a question the run never asked);
- `missing`: some reply is in none of the caches;
- `unloadable`: its config no longer loads, or names a prompt file that has
  since gone, so it can't be replayed.

`replay(run_dir, archive, out)` plays one run again from an archive alone and
returns the new run's folder, which holds its full `turns.jsonl`.
"""

import contextlib
import json
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

from collusion_lab import backends
from collusion_lab.cache import Cache
from collusion_lab.config import load_config
from collusion_lab.runner import run_config, run_sweep

STATES = ("reproduced", "differs", "missing", "unloadable")


@dataclass(frozen=True)
class RunResult:
    run: str
    state: str
    keys: int  # replies the replay read


class NotArchived(Exception):
    """A call no cache could answer; a 404, so the run stops at once."""

    status_code = 404


class Merged(Cache):
    """Every reply in some caches, read-only, noting the reply each key gave.

    Caches in different checkouts each sampled their own replies, so one key
    can hold several; the first cache's wins unless `prefer` names another."""

    def __init__(self, paths=()):
        super().__init__(Path("unused.sqlite"), "use")
        self.records, self.used, self.prefer = {}, {}, None
        for source, path in enumerate(paths):
            with contextlib.closing(sqlite3.connect(path)) as db:
                for key, reply in db.execute("SELECT key, reply FROM replies"):
                    self.add(key, reply, source)

    def add(self, key, reply, source=0):
        options = self.records.setdefault(key, [])
        if all(reply != other for _, other in options):
            options.append((source, reply))

    def get(self, key):
        if not (options := self.records.get(key)):
            return None
        reply = next((r for s, r in options if s == self.prefer), options[0][1])
        self.used[key] = reply
        return json.loads(reply)

    def rivals(self):
        """Caches holding another reply for a key the last replay read."""
        sources = set()
        for key, chosen in self.used.items():
            sources |= {s for s, r in self.records[key] if r != chosen}
        return sorted(sources)


@contextlib.contextmanager
def offline():
    """No call reaches a model while this is open."""

    async def refuse(**request):
        raise NotArchived(f"{request.get('model')}: not in the archive")

    called, backends._acompletion = backends._acompletion, refuse
    try:
        yield
    finally:
        backends._acompletion = called


def pack(root, caches, out):
    """Archive the replies behind every run under `root`; a RunResult each."""
    root, merged = Path(root), Merged(caches)
    results, index = [], []
    with tempfile.TemporaryDirectory() as scratch:
        for config_path in sorted(root.rglob("config.yaml")):
            result = _check(root, config_path, merged, Path(scratch))
            results.append(result)
            index += [
                (result.run, key, merged.used[key]) for key in sorted(merged.used)
            ]
    _write(out, index)
    return results


def _check(root, config_path, merged, scratch):
    """Replay one committed run offline against the merged caches, and again
    with each cache that answered some key differently put first, until one
    reproduces it; the attempt kept leaves its replies in `merged.used`."""
    merged.prefer = None
    result, used = _attempt(root, config_path, merged, scratch), dict(merged.used)
    for source in merged.rivals() if result.state in ("differs", "missing") else ():
        merged.prefer = source
        again = _attempt(root, config_path, merged, scratch / str(source))
        if again.state == "reproduced":
            return again
    merged.used = used
    return result


def _attempt(root, config_path, merged, scratch):
    """One offline replay of a committed run."""
    run_dir = config_path.parent
    run = run_dir.relative_to(root).as_posix()
    merged.used = {}
    try:
        config = load_config(config_path)
    except Exception:  # noqa: BLE001  an old config, whatever is wrong with it
        return RunResult(run, "unloadable", 0)
    try:
        with offline():
            [outcome] = run_sweep(config, scratch / run, merged)
    except Exception:  # noqa: BLE001  a prompt file gone, say: it can't be replayed
        return RunResult(run, "unloadable", len(merged.used))
    if outcome.state == "failed":
        return RunResult(run, "missing", len(merged.used))
    state = "reproduced" if _same(run_dir, outcome.dir) else "differs"
    return RunResult(run, state, len(merged.used))


def replay(run_dir, archive, out):
    """Play a committed run again from an archive alone, with the replies the
    archive keeps for it; its new folder."""
    run_dir = Path(run_dir)
    config = load_config(run_dir / "config.yaml")
    merged = Merged()
    with contextlib.closing(sqlite3.connect(archive)) as db:
        rows = db.execute(
            "SELECT runs.run, replies.key, replies.reply FROM runs"
            " JOIN replies ON replies.id = runs.reply"
        ).fetchall()
    mine = [(k, r) for run, k, r in rows if run_dir.as_posix().endswith(run)]
    for key, reply in mine or [(k, r) for _, k, r in rows]:
        merged.add(key, reply)
    with offline():
        [played] = run_config(config, out, merged)
    return played


def _same(committed, replayed):
    """Whether two runs made the same decisions, turn for turn."""
    return _decisions(committed) == _decisions(replayed)


def _decisions(run_dir):
    for name in ("turns.compact.jsonl", "turns.jsonl"):
        if (path := Path(run_dir) / name).exists():
            lines = [json.loads(line) for line in path.read_text().splitlines()]
            return [(t["round"], t["phase"], t["agent"], t.get("used")) for t in lines]
    return None


def _write(out, index):
    """`replies (id, key, reply)`, each distinct reply once, and `runs (run,
    key, reply)`, the reply each run read for each key."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    ids = {}
    for _, key, reply in index:
        ids.setdefault((key, reply), len(ids) + 1)
    with contextlib.closing(sqlite3.connect(out)) as db:
        db.execute(
            "CREATE TABLE replies (id INTEGER PRIMARY KEY, key TEXT, reply TEXT)"
        )
        db.execute("CREATE TABLE runs (run TEXT, key TEXT, reply INTEGER)")
        db.executemany(
            "INSERT INTO replies VALUES (?, ?, ?)",
            [(i, key, reply) for (key, reply), i in ids.items()],
        )
        db.executemany(
            "INSERT INTO runs VALUES (?, ?, ?)",
            [(run, key, ids[(key, reply)]) for run, key, reply in index],
        )
        db.commit()
