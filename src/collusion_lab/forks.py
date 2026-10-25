# Implements: runs/fork-pointers
"""A committed fork kept as its own turns plus a pointer to its base.

A run forked from another (E9's arms replay one base game up to the round-10
audit, then go their own way) shares the base's first compact lines. Packed
(`reports/pack_forks.py`), its `turns.compact.jsonl` holds only the lines
after those, and `fork.json` says where the rest is: `base`, the base run's
folder relative to the fork's, `lines`, how many of the base's compact lines
come first, and `round`, the first round of the fork's own (for a reader of
the file; the lines decide), and `sha256`, the whole log's hash, so a test
can check every rebuilt log against the one that was packed. `compact_text(run)` rebuilds the full compact
log, byte for byte as it was before packing; every reader of a compact log
goes through it.
"""

import hashlib
import json
import os
from pathlib import Path

COMPACT = "turns.compact.jsonl"
POINTER = "fork.json"


def compact_text(run):
    """A run's whole compact log, its base's shared lines first if it's a fork."""
    run = Path(run)
    own = (run / COMPACT).read_text()
    pointer = run / POINTER
    if not pointer.exists():
        return own
    fork = json.loads(pointer.read_text())
    base = compact_text(run / fork["base"]).splitlines(keepends=True)
    return "".join(base[: fork["lines"]]) + own


def digest(text):
    """The SHA-256 of a whole compact log, as `fork.json` records it."""
    return hashlib.sha256(text.encode()).hexdigest()


def compact_lines(run):
    """The compact log's lines, without their line ends."""
    return [line for line in compact_text(run).splitlines() if line]


def compact_turns(run):
    return [json.loads(line) for line in compact_lines(run)]


def shared(base, run):
    """How many leading compact lines `run` has in common with `base`."""
    ours = compact_text(run).splitlines(keepends=True)
    theirs = compact_text(base).splitlines(keepends=True)
    n = 0
    for a, b in zip(ours, theirs, strict=False):
        if a != b:
            break
        n += 1
    return n


def pack(base, run, lines):
    """Keep `run` as its own lines past the first `lines` of `base`, plus a
    pointer; undo it and return False unless the rebuilt log is the same."""
    run, base = Path(run), Path(base)
    original = compact_text(run)
    kept = original.splitlines(keepends=True)
    first = json.loads(kept[lines])["round"] if lines < len(kept) else None
    pointer = {
        "base": os.path.relpath(base, run),
        "lines": lines,
        "round": first,
        "sha256": digest(original),
    }
    (run / POINTER).write_text(json.dumps(pointer) + "\n")
    (run / COMPACT).write_text("".join(kept[lines:]))
    if compact_text(run) == original:
        return True
    (run / COMPACT).write_text(original)
    (run / POINTER).unlink()
    return False
