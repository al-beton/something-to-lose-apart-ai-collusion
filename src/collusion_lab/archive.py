# Implements: reproducibility/cache-archive
"""One archive of the cached replies behind every committed run, and offline
replay from it.

Replies live in response caches (see cache.py), one per checkout, so nobody
else can replay our runs from them. `pack(root, caches, out)` merges the
caches it is given and replays every committed run under `root` (each folder
with a `config.yaml`) against them, offline: a call the caches can't answer
fails the run rather than reaching a model. The replies each replay read are
written to `out`, an SQLite file with the cache's own `replies` table plus
`runs (run, key)`, the index from each run to its replies.

Each run ends in one state:
- `reproduced`: every reply was there, and the replay made the same move
  and message, turn for turn, as the run's committed log;
- `differs`: every reply was there, but the replay's decisions differ (a
  prompt file edited since the run changes what is asked, so its replies
  answer a question the run never asked);
- `missing`: some reply is in none of the caches;
- `unloadable`: its config no longer loads.

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
    """Every reply in some caches, read-only, noting which keys are read."""

    def __init__(self, paths):
        super().__init__(Path("unused.sqlite"), "use")
        self.records, self.used = {}, set()
        for path in paths:
            with contextlib.closing(sqlite3.connect(path)) as db:
                for key, reply in db.execute("SELECT key, reply FROM replies"):
                    self.records.setdefault(key, reply)

    def get(self, key):
        if key not in self.records:
            return None
        self.used.add(key)
        return json.loads(self.records[key])

    def put(self, key, record):
        pass  # offline: nothing new is ever stored


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
            index += [(result.run, key) for key in sorted(merged.used)]
    _write(out, merged, index)
    return results


def _check(root, config_path, merged, scratch):
    """Replay one committed run offline against the merged caches."""
    run_dir = config_path.parent
    run = run_dir.relative_to(root).as_posix()
    merged.used = set()
    try:
        config = load_config(config_path)
    except Exception:  # noqa: BLE001  an old config, whatever is wrong with it
        return RunResult(run, "unloadable", 0)
    with offline():
        [outcome] = run_sweep(config, scratch / run, merged)
    if outcome.state == "failed":
        return RunResult(run, "missing", len(merged.used))
    state = "reproduced" if _same(run_dir, outcome.dir) else "differs"
    return RunResult(run, state, len(merged.used))


def replay(run_dir, archive, out):
    """Play a committed run again from an archive alone; its new folder."""
    config = load_config(Path(run_dir) / "config.yaml")
    with offline():
        [played] = run_config(config, out, Merged([archive]))
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


def _write(out, merged, index):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    keys = sorted({key for _, key in index})
    with contextlib.closing(sqlite3.connect(out)) as db:
        db.execute("CREATE TABLE replies (key TEXT PRIMARY KEY, reply TEXT)")
        db.execute("CREATE TABLE runs (run TEXT, key TEXT)")
        db.executemany(
            "INSERT INTO replies VALUES (?, ?)", [(k, merged.records[k]) for k in keys]
        )
        db.executemany("INSERT INTO runs VALUES (?, ?)", index)
        db.commit()
