# Implements: runs/digest, ci/results-digest, ci/numbers-checked
"""`lab digest`: every registered experiment's results on one Markdown page.

`registry()` reads `reports/experiments.yaml` (one entry per experiment:
name, run folders, grouping, headline window, findings note). `digest()`
writes, for the experiments given (all, or `changed(since)`: those whose
runs or note differ from a git ref, and the registry's `sample` experiment
when the code that computes or draws results changed), a page that reads inline on GitHub: a
summary table first, then each experiment folded away in `<details>`, with
its `lab analyse` table (a text strip of every game's gain in each row), a
Mermaid `xychart-beta` bar chart of each cell's mean gain and up to three of
its indexed moments (`reports/moments.yaml`). It never calls a model, and it
stays within a comment's size (`LIMIT`): sections past it are cut with a
note saying so.

`check()` recomputes every number the notes mark, written
`<!-- check: CELL | COLUMN = VALUE -->` with CELL and COLUMN as `lab
analyse` names them and VALUE as it prints, and returns each mismatch.
"""

import re
import subprocess
from pathlib import Path

import yaml

from collusion_lab.analysis import analyse, printable
from collusion_lab.summary import cell as shown

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "reports" / "experiments.yaml"
MOMENTS = ROOT / "reports" / "moments.yaml"
LIMIT = 60_000  # characters; a GitHub comment holds 65,536
MOMENTS_SHOWN = 3
COLUMNS = (
    "cell",
    "games",
    "gain",
    "clipped gain",
    "95% CI",
    "sd",
    "games above Nash",
    "explicit",
    "tacit",
    "owned up",
    "false confessions",
    "free time kept/lost",
    "each game",
)
# Code whose change alters what the digest shows: the sample experiment
# (`sample: true` in the registry) is digested for it.
RESULTS_CODE = (
    "src/collusion_lab/analysis.py",
    "src/collusion_lab/digest.py",
    "src/collusion_lab/summary.py",
    "src/collusion_lab/charts.py",
    "src/collusion_lab/report/",
    "reports/experiments.yaml",
)
CHECK = re.compile(r"<!--\s*check:\s*(.+?)\s*\|\s*(.+?)\s*=\s*(.+?)\s*-->")


def registry(path=None):
    return yaml.safe_load(Path(path or REGISTRY).read_text()) or []


def changed(experiments, since, root=None):
    """The experiments whose run folders or note changed since git ref `since`."""
    root = root or ROOT
    paths = subprocess.run(
        ["git", "diff", "--name-only", f"{since}...HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    found = [e for e in experiments if any(_touches(e, p) for p in paths)]
    # A change to how results are computed or drawn shows on the sample.
    if any(p.startswith(RESULTS_CODE) for p in paths):
        found += [e for e in experiments if e.get("sample") and e not in found]
    return found


def rows_of(experiment, root=None):
    """The `lab analyse` rows of an experiment; with several folders, each
    cell is named by its folder too, so treatments never merge or collide."""
    root = root or ROOT
    found, folders = [], experiment["runs"]
    for folder in folders:
        rows = analyse(
            Path(root) / folder, experiment.get("by"), experiment.get("rounds")
        )
        if len(folders) > 1:
            for r in rows:
                r["cell"] = f"{Path(folder).name} / {r['cell']}"
        found += rows
    return found


def digest(experiments, root=None, title="Results digest"):
    """The Markdown page for `experiments`, within LIMIT characters."""
    root = root or ROOT
    computed = [(e, rows_of(e, root)) for e in experiments]
    summary = [
        "| experiment | cells | games | gain, lowest to highest cell | window |",
        "|---|---|---|---|---|",
    ]
    for e, rows in computed:
        gains = [r["gain"] for r in rows]
        span = f"{min(gains):+.2f} to {max(gains):+.2f}" if gains else "—"
        games = sum(r["games"] for r in rows)
        window = e.get("rounds") or "last rounds"
        summary.append(f"| {e['name']} | {len(rows)} | {games} | {span} | {window} |")
    head = f"## {title}\n\nNo model was called: every number is read from committed runs.\n\n"
    page = head + "\n".join(summary) + "\n"
    if not experiments:
        return head + "No registered experiment changed.\n"
    for e, rows in computed:
        section = _section(e, rows, root)
        if len(page) + len(section) > LIMIT:
            page += f"\n*{e['name']} and the rest were cut to fit a comment; run `lab digest` for them.*\n"
            break
        page += section
    return page


def check(experiments, root=None):
    """Every marked number in the notes that the runs don't give, as a line."""
    root = root or ROOT
    problems = []
    for e in experiments:
        note = e.get("note")
        if not note or not (Path(root) / note).exists():
            continue
        marks = CHECK.findall((Path(root) / note).read_text())
        if not marks:
            continue
        rows = {r["cell"]: r for r in printable(rows_of(e, root))}
        for cell, column, value in marks:
            row = rows.get(cell)
            if row is None:
                problems.append(f"{note}: no cell {cell!r} in {e['name']}")
            elif column not in row:
                problems.append(f"{note}: no column {column!r}")
            elif shown(row[column]) != value:
                problems.append(
                    f"{note}: {cell} | {column} is {shown(row[column])}, "
                    f"the note says {value}"
                )
    return problems


def _touches(experiment, path):
    owned = [*experiment["runs"], experiment.get("note") or "\0"]
    return any(path == p or path.startswith(p.rstrip("/") + "/") for p in owned)


def _section(experiment, rows, root):
    rows = printable(rows)
    games = sum(r["games"] for r in rows)
    note = experiment.get("note")
    opening = (
        f"\n<details><summary><b>{experiment['name']}</b>: {len(rows)} cells, "
        f"{games} games</summary>\n"
    )
    lines = [opening]
    if note:
        lines.append(f"Findings: [`{note}`]({note}).\n")
    lines += [
        "| # | " + " | ".join(COLUMNS) + " |",
        "|---|" + "---|" * len(COLUMNS),
    ]
    for n, r in enumerate(rows, 1):
        values = [_short(r[c]) if c == "cell" else shown(r[c]) for c in COLUMNS]
        lines.append(
            f"| {n} "
            + "| "
            + " | ".join(
                f"`{v}`" if c == "each game" else str(v)
                for c, v in zip(COLUMNS, values, strict=True)
            )
            + " |"
        )
    lines += ["", _chart(rows), *_moments(experiment, root), "</details>\n"]
    return "\n".join(lines)


def _chart(rows):
    """A Mermaid bar chart of each cell's clipped gain, cells numbered as in
    the table. Mermaid draws bars up from the axis's foot, so a negative gain
    would read as a positive bar: the chart shows gain clipped to 0..1, and
    the table the gain itself."""
    names = ", ".join(f'"{n}"' for n in range(1, len(rows) + 1))
    gains = ", ".join(f"{r['clipped gain']:.3f}" for r in rows)
    return (
        "```mermaid\nxychart-beta\n"
        '    title "Gain by cell, clipped to 0 (Nash) .. 1 (joint profit)"\n'
        f"    x-axis [{names}]\n"
        '    y-axis "clipped gain" 0 --> 1\n'
        f"    bar [{gains}]\n```\n"
    )


def _moments(experiment, root):
    if not (Path(root) / "reports" / "moments.yaml").exists():
        return []
    moments = (
        yaml.safe_load((Path(root) / "reports" / "moments.yaml").read_text()) or []
    )
    mine = [
        m
        for m in moments
        if any(
            str(m.get("run", "")).startswith(f.rstrip("/") + "/")
            for f in experiment["runs"]
        )
    ][:MOMENTS_SHOWN]
    if not mine:
        return []
    quoted = [
        f"> {m['quote']}\n> — {str(m['model']).split('/')[-1]}, round {m['round']} "
        f"{m['phase']}, firm {m['firm']} (`{m['label']}`)\n"
        for m in mine
    ]
    return ["**Moments**\n", *quoted]


def _short(cell):
    """A cell's name with each path or model id cut to its last part."""
    parts = str(cell).split(" / ")
    return " / ".join(p.rsplit("/", 1)[-1].removesuffix(".md") for p in parts)
