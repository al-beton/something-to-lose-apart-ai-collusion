"""Draft an experiment's findings note from its committed runs.

Implements: research/findings-note

Run from the repository root, once the experiment's runs are committed:
`uv run python reports/note.py runs/<experiment> [--out FILE] [--force]`
It writes `reports/<experiment>/findings.md` (the folder's name is the
experiment's) and refuses to overwrite a note that's already there, since
the Researcher edits it; `--force` starts it again.

The draft holds what the runs can say on their own:
- an `Implements:` line naming every statement of the experiment's spec,
  `experiments/spec/<experiment>.md`, when there is one;
- how many runs and what they cost, from their manifests;
- the `lab summary` table, grouped by the swept values;
- the first few highlights, as on a report's first screen;
- how often models said they might be under evaluation (the table's
  `eval-aware` column), when the runs counted it;
- the moments `reports/moments.yaml` indexes in these runs, with their quotes.

The short answer, the question and budget, the hypotheses and what the
experiment can't show are left as prompts starting "_To write:", for the
Researcher; every number above stays traceable to the runs.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml

from collusion_lab.report.markdown import first_screen_markdown
from collusion_lab.summary import cell, format_table, group_runs, run_cost, summarize

MOMENTS = Path("reports/moments.yaml")
SPECS = Path("experiments/spec")
STATEMENT = re.compile(r"^- \*\*([a-z0-9-]+):\*\*", re.MULTILINE)


def draft(folder, moments=MOMENTS, spec=None):
    """The note's text for the runs under `folder`."""
    folder = Path(folder)
    name = folder.name
    spec = Path(spec) if spec else SPECS / f"{name}.md"
    by, _ = group_runs(folder)
    rows = summarize(folder)
    parts = [
        *_implements(spec),
        f"# {name}: findings (draft, {date.today():%d %b})",
        "",
        "## Short answer",
        "",
        "_To write: what we found, in two or three plain sentences._",
        "",
        "## Question and budget",
        "",
        f"_To write: the question, arms and cap from `{spec}`._",
        "",
        _runs_line(folder, rows),
        "",
        "## Results",
        "",
        format_table(rows),
        "",
        "## Top highlights",
        "",
        _highlights(folder),
        "",
        "## Eval-awareness",
        "",
        _eval_awareness(by, rows),
        "",
        "## Moments",
        "",
        *_moments(folder, moments),
        "",
        "## Hypotheses",
        "",
        "_To write: what might explain it, and what would tell them apart._",
        "",
        "## What it can't show",
        "",
        "_To write: the limits, plainly (seeds, models, prompts, scoring rules)._",
    ]
    return "\n".join(parts) + "\n"


def _implements(spec):
    if not spec.exists():
        return []
    names = STATEMENT.findall(spec.read_text())
    area = spec.stem
    return [f"<!-- Implements: {', '.join(f'{area}/{n}' for n in names)} -->"]


def _runs_line(folder, rows):
    _, groups = group_runs(folder)
    runs = [r for _, rs in groups for r in rs]
    unknown = any(r.manifest.get("cost") is None for r in runs if r.manifest)
    cost = sum(run_cost(r.manifest) for r in runs)
    spent = f"cost ${cost:.4f}" + (" (some calls unpriced)" if unknown else "")
    return f"{len(runs)} runs in `{folder}` across {len(rows)} arms, {spent}."


def _highlights(folder):
    """The first screen's highlights, without its title, sentences or table."""
    screen = first_screen_markdown(folder)
    return screen[screen.index("**Highlights**") + len("**Highlights**") :].strip()


def _eval_awareness(by, rows):
    counted = [r for r in rows if r.get("eval-aware") is not None]
    if not counted:
        return "Eval-awareness was not counted in these runs."
    lines = ["Share of model turns that mention being evaluated, per arm:", ""]
    for row in counted:
        arm = ", ".join(f"{k} = {cell(row[k])}" for k in by) or "all runs"
        lines.append(f"- {arm}: {row['eval-aware']}")
    return "\n".join(lines)


def _moments(folder, moments):
    path = Path(moments)
    found = []
    if path.exists():
        inside = folder.resolve()
        for m in yaml.safe_load(path.read_text()) or []:
            run = Path(m["run"]).resolve()
            if run == inside or inside in run.parents:
                found.append(m)
    if not found:
        return [f"_To write: index this experiment's moments in `{path}`._"]
    return [
        f"- **{m['label']}** ({m['model']}, `{m['run']}`, round {m['round']} "
        f'{m["phase"]}, firm {m["firm"]}): "{m["quote"]}"'
        for m in found
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("folder", help="the experiment's runs, e.g. runs/stakes")
    parser.add_argument("--out", help="default reports/<experiment>/findings.md")
    parser.add_argument("--moments", default=str(MOMENTS))
    parser.add_argument("--spec", help="default experiments/spec/<experiment>.md")
    parser.add_argument("--force", action="store_true", help="overwrite a note")
    args = parser.parse_args(argv)
    folder = Path(args.folder)
    out = Path(args.out or f"reports/{folder.name}/findings.md")
    if out.exists() and not args.force:
        print(f"{out} exists and may hold edits; pass --force to draft it again.")
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(draft(folder, args.moments, args.spec))
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
