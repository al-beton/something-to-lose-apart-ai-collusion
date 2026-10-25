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
  since gone with no file of the same text left (`load_run_config` finds a
  moved prompt again by the SHA-256 its manifest recorded), so it can't be
  replayed.

`replay(run_dir, archive, out)` plays one run again from an archive alone and
returns the new run's folder, which holds its full `turns.jsonl`.
"""

import contextlib
import dataclasses
import functools
import gzip
import hashlib
import json
import shutil
import sqlite3
import subprocess
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
    a RunResult each. Runs are named from the `runs` folder `root` is in, so
    packing one part of it (`runs/<experiment>`) replaces that part alone."""
    root, merged = Path(root).resolve(), Merged(caches)
    base = _base(root)
    results, index = [], []
    with tempfile.TemporaryDirectory() as scratch:
        for config_path in sorted(root.rglob("config.yaml")):
            result = _check(base, config_path, merged, Path(scratch))
            results.append(result)
            index += [
                (result.run, key, merged.used[key]) for key in sorted(merged.used)
            ]
    part = None if root == base else root.relative_to(base).as_posix()
    _write(out, index, {r.run: r.state for r in results}, limit, part)
    return results


def _base(root):
    """The `runs` folder `root` is, or is in; `root` itself if none."""
    return next((f for f in (root, *root.parents) if f.name == "runs"), root)


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
        config = load_run_config(run_dir)
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


def load_run_config(run_dir):
    """A committed run's config, with the prompts it actually read: each
    prompt file its manifest recorded (an agent's or a condition's), when it
    has since moved or been edited in place, is put back at its recorded path
    with the text of that SHA-256, taken from the file that now holds it or
    from git history, in a copy of the prompts folder the config then reads.
    So a replay asks exactly what the run asked."""
    run_dir = Path(run_dir)
    config = load_config(run_dir / "config.yaml")
    prompts = Path(config.prompts_dir)
    if not prompts.is_absolute():
        prompts = Path.cwd() / prompts
    manifest = run_dir / "manifest.json"
    recorded = (
        json.loads(manifest.read_text()).get("prompts", {}) if manifest.exists() else {}
    )
    restored = {}
    for name, digest in recorded.items():
        path = prompts / name
        if path.exists() and _digest(path.read_bytes()) == digest:
            continue
        text = _same_text(prompts, digest) or _from_history(prompts, name, digest)
        if text is not None:
            restored[name] = text
    if restored:
        config = dataclasses.replace(
            config, prompts_dir=str(_overlay(prompts, restored))
        )
    return config


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _same_text(prompts, digest):
    """The text of the prompt file under `prompts` whose SHA-256 is
    `digest`, wherever it now lives, or None."""
    for path in sorted(prompts.rglob("*.md")):
        if _digest(text := path.read_bytes()) == digest:
            return text
    return None


@functools.cache
def _from_history(prompts, name, digest):
    """The text a prompt file had when its SHA-256 was `digest`, from git
    history, or None when no commit kept it."""
    path = (prompts / name).resolve()

    def git(*args, cwd=prompts):  # the prompts folder exists; the file's may not
        found = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, check=False
        )
        return found.stdout if found.returncode == 0 else b""

    top = Path(git("rev-parse", "--show-toplevel").decode().strip() or prompts)
    if not path.is_relative_to(top):
        return None
    rel = path.relative_to(top).as_posix()  # git reads paths from the top
    for commit in (
        git("log", "--all", "--format=%H", "--", rel, cwd=top).decode().split()
    ):
        text = git("show", f"{commit}:{rel}", cwd=top)
        if text and _digest(text) == digest:
            return text
    return None


@functools.cache
def _overlay_root():
    return Path(tempfile.mkdtemp(prefix="prompts-as-run-"))


def _overlay(prompts, edited):
    """A copy of `prompts` with the given files, at their recorded paths, at
    the versions a run read."""
    key = _digest(
        json.dumps(sorted((n, _digest(t)) for n, t in edited.items())).encode()
    )
    folder = _overlay_root() / key[:16]
    if not folder.exists():
        shutil.copytree(prompts, folder)
        for name, text in edited.items():
            (folder / name).parent.mkdir(parents=True, exist_ok=True)
            (folder / name).write_bytes(text)
    return folder


def replay(run_dir, archive, out):
    """Play a committed run again from an archive folder alone, with the
    replies it keeps for that run; its new folder."""
    run_dir, archive = Path(run_dir), Path(archive)
    config = load_run_config(run_dir)
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


def _write(out, index, states, limit, part=None):
    """`out/<experiment>[-n].jsonl.gz`: one line per (run, key, reply), each
    file holding whole runs and under `limit` bytes; `out/index.json`: each
    run's file and state. With `part` (a folder under `runs`), only the runs
    under it are replaced (see `_rest`)."""
    out, states = Path(out), dict(states)
    out.mkdir(parents=True, exist_ok=True)
    lines = {}
    for run, key, reply in index:
        line = json.dumps({"run": run, "key": key, "reply": reply}, ensure_ascii=False)
        lines.setdefault(run, []).append(line + "\n")
    runs, stale = {}, list(out.glob("*.jsonl.gz"))
    if part is not None:
        runs, stale = _rest(out, part, lines, states)
    for path in [*stale, out / "index.json"]:
        path.unlink(missing_ok=True)
    files = {}
    for run in sorted(states):
        experiment = run.split("/")[0]
        chunk = gzip.compress("".join(lines.get(run, [])).encode(), mtime=0)
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
    runs = dict(sorted(runs.items()))
    (out / "index.json").write_text(json.dumps({"runs": runs}, indent=1) + "\n")


def _rest(out, part, lines, states):
    """What packing `part` alone keeps of the archive in `out`: the index
    entries of every experiment it doesn't touch, as they are, and the files
    of those it does, to be written again. The touched experiments' runs
    outside `part` keep their replies and states, added to `lines` and
    `states`."""
    path = out / "index.json"
    old = json.loads(path.read_text())["runs"] if path.exists() else {}
    touched = {run.split("/")[0] for run in [*states, part]}
    kept = {r: v for r, v in old.items() if r.split("/")[0] not in touched}
    redone = sorted({v["file"] for r, v in old.items() if r not in kept})

    def outside(run):
        return run != part and not run.startswith(f"{part}/")

    for run, entry in old.items():
        if run not in kept and outside(run):
            states[run] = entry["state"]
    for name in redone:
        with gzip.open(out / name, "rt") as replies:
            for text in replies:
                if outside(run := json.loads(text)["run"]):
                    lines.setdefault(run, []).append(text)
    return kept, [out / name for name in redone]
