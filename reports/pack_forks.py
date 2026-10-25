"""Keep a folder's forked runs as their own turns plus a pointer to a base.

Implements: runs/fork-pointers, specs-and-docs/runs-are-evidence

`uv run python reports/pack_forks.py FOLDER` walks the committed runs under
FOLDER in path order. A run whose compact log shares at least half its lines
(and at least MIN_SHARED) with an earlier run of the same seed, kept whole,
is packed against the one it shares the most with (`forks.pack`); any other
becomes a base itself. A run whose rebuilt log would differ in a single byte
is left as it was and named. Running it again changes nothing.
"""

import json
import sys
from pathlib import Path

from collusion_lab import forks

MIN_SHARED = 10


def main(folder):
    bases, packed, refused = {}, 0, []
    for summary in sorted(Path(folder).rglob("summary.json")):
        run = summary.parent
        pointer = run / forks.POINTER
        if pointer.exists():
            _record_hash(run, pointer)
            continue
        if not (run / forks.COMPACT).exists():
            continue
        total = len(forks.compact_lines(run))
        candidates = bases.setdefault(run.name, [])  # the seed, as seed-N
        best = max(candidates, key=lambda b: forks.shared(b, run), default=None)
        lines = forks.shared(best, run) if best else 0
        if lines >= MIN_SHARED and 2 * lines >= total:
            if forks.pack(best, run, lines):
                packed += 1
            else:
                refused.append(run)
        else:
            candidates.append(run)
    for run in refused:
        print(f"{run}: left whole, its rebuilt log would differ", file=sys.stderr)
    whole = sum(len(b) for b in bases.values())
    print(f"Packed {packed} forks against {whole} whole runs.")
    return 1 if refused else 0


def _record_hash(run, pointer):
    """A fork packed before pointers kept the whole log's hash gets it now,
    from its rebuilt log (which matched the original when it was packed)."""
    fork = json.loads(pointer.read_text())
    if "sha256" not in fork:
        fork["sha256"] = forks.digest(forks.compact_text(run))
        pointer.write_text(json.dumps(fork) + "\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
