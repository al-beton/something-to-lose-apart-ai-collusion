# Implements: runs/fork-pointers, reproducibility/cache-archive
"""One archive of the cached replies behind every committed run, and offline
replay from it.

Replies live in response caches (see cache.py), one per checkout, so nobody
else can replay our runs from them. `pack(root, caches, out)` merges the
caches it is given and replays every committed run under `root` (each folder
with a `config.yaml`) against them, offline: a call the caches can't answer
fails the run rather than reaching a model. The replies each replay read are
written to the folder `out` (see `_write`), with an index from each run to
its file.
Caches in different checkouts each sampled their own replies, so one request
can have several; a run that the first cache's replies don't reproduce is
replayed again with each disagreeing cache put first, and the archive keeps
the replies of the attempt that reproduced it.

Each run ends in one state:
- `reproduced`: every reply was there, and the replay made the same move
  and message, and gave the same free-time replies, turn for turn, as the
  run's committed log;
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
import gzip
import json
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

from collusion_lab import forks
from collusion_lab.backends import offline
from collusion_lab.cache import Cache
from collusion_lab.config import load_config
from collusion_lab.runner import run_config, run_sweep

STATES = ("reproduced", "differs", "missing", "unloadable")
LIMIT = 20_000_000  # bytes a committed archive file may hold


@dataclass(frozen=True)
class RunResult:
    run: str
    state: str
    keys: int  # replies the replay read


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
        self.records.setdefault(key, []).append((source, reply))

    def get(self, key):
        if not (options := self.records.get(key)):
            return None
        reply = next((r for s, r in options if s == self.prefer), options[0][1])
        self.used[key] = reply
        return json.loads(reply)

    def put(self, key, record):
        pass  # offline and read-only: nothing new is ever stored

    def label(self, key, about):
        pass  # nor are old replies relabelled

    def rivals(self):
        """Caches holding another reply for a key the last replay read."""
        sources = set()
        for key, chosen in self.used.items():
            sources |= {s for s, r in self.records[key] if r != chosen}
        return sorted(sources)


def pack(root, caches, out, limit=LIMIT):
    """Archive the replies behind every run under `root` in the folder `out`;
    a RunResult each."""
    root, merged = Path(root), Merged(caches)
    results, index = [], []
    with tempfile.TemporaryDirectory() as scratch:
        for config_path in sorted(root.rglob("config.yaml")):
            result = _check(root, config_path, merged, Path(scratch))
            results.append(result)
            index += [
                (result.run, key, merged.used[key]) for key in sorted(merged.used)
            ]
    _write(out, index, {r.run: r.state for r in results}, limit)
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
    """Play a committed run again from an archive folder alone, with the
    replies it keeps for that run; its new folder."""
    run_dir, archive = Path(run_dir), Path(archive)
    config = load_config(run_dir / "config.yaml")
    index = json.loads((archive / "index.json").read_text())["runs"]
    run = find_run(run_dir, index)
    merged = Merged()
    with gzip.open(archive / index[run]["file"], "rt") as lines:
        for line in map(json.loads, lines):
            if line["run"] == run:
                merged.add(line["key"], line["reply"])
    with offline():
        [played] = run_config(config, out, merged)
    return played


def find_run(run_dir, index):
    """The run in `index` that `run_dir` ends with, path part for path part."""
    parts = Path(run_dir).resolve().parts
    found = [r for r in index if parts[-len(Path(r).parts) :] == Path(r).parts]
    if not found:
        raise KeyError(f"{run_dir} isn't in the archive")
    return max(found, key=lambda r: len(Path(r).parts))


def _same(committed, replayed):
    """Whether two runs made the same decisions, turn for turn. Older
    committed logs keep no free-time reply (nor session); for those turns
    only the turn itself can be compared."""
    ours, theirs = _decisions(committed), _decisions(replayed)
    if ours is None or theirs is None or len(ours) != len(theirs):
        return ours == theirs
    return all(
        a == b or (len(a) > 4 and a[-1] is None and a[:4] == b[:4])
        for a, b in zip(ours, theirs, strict=True)
    )


def _decisions(run_dir):
    if (Path(run_dir) / forks.COMPACT).exists():
        return [_decision(t) for t in forks.compact_turns(run_dir)]
    if (path := Path(run_dir) / "turns.jsonl").exists():
        lines = [json.loads(line) for line in path.read_text().splitlines()]
        return [_decision(t) for t in lines]
    return None


def _decision(turn):
    """What a turn decided: its move and message, or for free time, which
    uses no move, its session's reply (only compacted logs keep the puzzle
    and score, both worked out from the request and reply)."""
    move = (turn["round"], turn["phase"], turn["agent"], turn.get("used"))
    if turn["phase"] != "leisure":
        return move
    return (*move, turn.get("session"), turn.get("reply"))


def _write(out, index, states, limit):
    """`out/<experiment>[-n].jsonl.gz`: one line per (run, key, reply), each
    file holding whole runs and under `limit` bytes; `out/index.json`: each
    run's file and state."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for old in [*out.glob("*.jsonl.gz"), out / "index.json"]:
        old.unlink(missing_ok=True)
    by_run = {}
    for run, key, reply in index:
        line = json.dumps({"run": run, "key": key, "reply": reply}, ensure_ascii=False)
        by_run.setdefault(run, []).append(line + "\n")
    files, runs = {}, {}
    for run in sorted(states):
        experiment = run.split("/")[0]
        chunk = gzip.compress("".join(by_run.get(run, [])).encode())
        parts = files.setdefault(experiment, [[]])
        if parts[-1] and sum(map(len, parts[-1])) + len(chunk) > limit:
            parts.append([])
        parts[-1].append(chunk)
        n = len(parts)
        runs[run] = {
            "file": f"{experiment}.jsonl.gz"
            if n == 1
            else f"{experiment}-{n}.jsonl.gz",
            "state": states[run],
        }
    for experiment, parts in files.items():
        for n, chunks in enumerate(parts, 1):
            name = f"{experiment}.jsonl.gz" if n == 1 else f"{experiment}-{n}.jsonl.gz"
            (out / name).write_bytes(b"".join(chunks))  # gzip members concatenate
    (out / "index.json").write_text(json.dumps({"runs": runs}, indent=1) + "\n")
