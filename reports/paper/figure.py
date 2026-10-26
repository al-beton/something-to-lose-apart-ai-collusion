"""One figure at a time: redraw it free from committed runs, or play its runs
again at cost.

Implements: reproducibility/figure-commands

`FIGURES` is the registry: each figure's id, what it shows, the
builder in `figures.py` that draws it, the files it draws, the `figures.py`
folders it reads, and which committed runs lie behind it. From the
repository root:

- `make figure F=ID` (`figure.py replay ID`) draws the figure into a scratch
  folder from the committed runs, calls no model, and fails unless every file
  it draws matches the committed one byte for byte;
- `make regenerate F=ID` (`figure.py regenerate ID [--yes] [--max-cost D]
  [--out DIR]`) plays every run behind the figure again with fresh calls into
  `runs/regenerated/ID/` (or `--out`), one run at a time through one new
  response cache there, so forks that shared a history share a fresh one;
  then draws the figure from those runs into its `figures/`. It says first how
  many games and calls that is and the most it should cost (each run's
  `lab run` estimate, summed: shared histories come from the cache, so less is
  spent), and that a fresh run is a new sample;
- `figure.py --list` prints the registry; `make figure-lines` rewrites the
  paper's table of these commands (between `BEGIN` and `END` in
  `paper/paper.md`) from it.

A run already finished in the output folder is kept, so a stopped
regeneration resumes. Each run's spend cap is what is left of `--max-cost`.
"""

import argparse
import dataclasses
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from collusion_lab import provenance
from collusion_lab.archive import load_run_config
from collusion_lab.cache import Cache
from collusion_lab.estimate import estimate
from collusion_lab.prices import price_for
from collusion_lab.runner import RunFailed, paid_calls, run_config

HERE = Path(__file__).resolve().parent
COMMITTED = HERE / "figures"
PAPER = Path("paper/paper.md")
BEGIN = "<!-- figure-commands: begin (make figure-lines writes this) -->"
END = "<!-- figure-commands: end -->"
NEW_SAMPLE = (
    "A fresh run is a new sample, not a replay: expect the counts to move "
    "(Gemma's own re-ask came forward 25 times in 96 where the paper has 20). "
    "Only self-hosted, batch-invariant inference reruns a game exactly; see "
    "REPRODUCIBILITY.md."
)


@dataclass(frozen=True)
class Figure:
    id: str
    shows: str  # what it shows, in a few words (the paper numbers figures)
    build: str  # its builder in figures.py
    name: str  # the files it draws: NAME.png, NAME.svg
    folders: tuple  # the figures.py folders it reads, by attribute name
    runs: Callable  # figures.py module -> the committed run folders behind it


def _e9_crux_runs(figs):
    """E9's games at a 90% review on the main seeds, in the figure's arms,
    with a model the figure draws (as `figures.e9_came_forward` keeps them)."""
    arms = {arm for arm, _ in figs.E9_ARMS}
    for summary in sorted(figs.E9.rglob("summary.json")):
        s = json.loads(summary.read_text())
        audit = s.get("audit")
        if not audit or audit["detection"] != 90 or s["seed"] not in figs.E9_SEEDS:
            continue
        arm = re.sub(r"^conditions-e9-|\.md$", "", summary.parts[-3].split("=")[-1])
        models = {a["model"].split("/")[-1] for a in audit["agents"].values()}
        if arm in arms and models & set(figs.MODELS):
            yield summary.parent


def _e4_runs(figs):
    """Every audited E4 fork, both the full study and the flat-fine confound."""
    for folder in (figs.E4, figs.E4_CONFOUND):
        for summary in sorted(folder.rglob("summary.json")):
            if json.loads(summary.read_text()).get("audit"):
                yield summary.parent


FIGURES = {
    f.id: f
    for f in (
        Figure(
            "e9-crux",
            "E9: coming forward, by personal stake",
            "fig3",
            "fig3-e9-came-forward",
            ("E9",),
            _e9_crux_runs,
        ),
        Figure(
            "e4-owning-up",
            "E4: owning up, by penalty schedule",
            "fig2",
            "fig2-e4-owning-up",
            ("E4", "E4_CONFOUND"),
            _e4_runs,
        ),
    )
}


def figures_module():
    spec = importlib.util.spec_from_file_location("paper_figures", HERE / "figures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def draw(figure, out, figs=None):
    """Draw `figure` into `out`; its files there, or [] if its data is absent."""
    figs = figs or figures_module()
    if not getattr(figs, figure.build)(Path(out)):
        return []
    return sorted(Path(out).glob(f"{figure.name}.*"))


def replay(figure, committed=COMMITTED):
    """One line per drawn file that differs from the committed one."""
    with tempfile.TemporaryDirectory() as scratch:
        drawn = draw(figure, scratch)
        if not drawn:
            return [f"{figure.name}: its committed runs aren't here"]
        return [
            f"{path.name}: differs from {committed / path.name}"
            for path in drawn
            if not (committed / path.name).exists()
            or (committed / path.name).read_bytes() != path.read_bytes()
        ]


@dataclass(frozen=True)
class Plan:
    runs: list  # (committed run folder, its config)
    calls: int
    cost: float | None  # the most it should cost; None when a model is unpriced
    unpriced: list


def plan(figure, figs=None):
    """The runs behind `figure` and what playing them all fresh would cost."""
    runs = [
        (run, load_run_config(run)) for run in figure.runs(figs or figures_module())
    ]
    calls, cost, unpriced = 0, 0.0, set()
    for _, config in runs:
        calls += paid_calls(config)
        guess = estimate(config, price_for)
        unpriced.update(guess.unpriced)
        cost += guess.cost or 0
    return Plan(runs, calls, None if unpriced else cost, sorted(unpriced))


def spend_line(figure, p):
    cost = (
        f"no price for {', '.join(p.unpriced)}, so no estimate"
        if p.cost is None
        else f"at most ${p.cost:.2f} estimated"
    )
    return f"{figure.id}: {len(p.runs)} games, {p.calls} model calls, {cost}."


def regenerate(figure, out, max_cost=None, yes=False, argv=()):
    """Play `figure`'s runs fresh into `out`, then draw it into `out/figures`."""
    load_dotenv(Path.cwd() / ".env")
    out = Path(out)
    if clash := _overwrites(out):
        print(f"figure: --out {out} would write over {clash}; pick another folder.")
        return 1
    figs = figures_module()
    p = plan(figure, figs)
    print(spend_line(figure, p))
    print(NEW_SAMPLE)
    print(f"Runs and the figure go to {out}/; nothing committed is touched.")
    if max_cost is not None and (p.cost is None or p.cost > max_cost):
        print(
            f"figure: the estimate isn't within the ${max_cost:g} spend cap; "
            "nothing was run.",
            file=sys.stderr,
        )
        return 1
    if not yes and not _agreed():
        return 1
    cache = Cache(out / "cache.sqlite", "use")
    started, spent, played = provenance.now(), 0.0, []
    for run, config in p.runs:
        relative = Path(run).resolve().relative_to(Path.cwd().resolve())
        target = out / relative
        if (target / "summary.json").exists():
            continue  # finished before: a stopped regeneration resumes
        if max_cost is not None:
            config = dataclasses.replace(config, budget=max_cost - spent)
        # A run plays in its own work folder, kept if it fails: the runner
        # resumes it there and counts what it already spent.
        work = out / WORK / relative
        try:
            [done] = run_config(config, work, cache)
        except RunFailed as error:
            partial = [m for m in work.rglob("manifest.json")]
            spent += sum(json.loads(m.read_text()).get("cost") or 0 for m in partial)
            played += [m.parent for m in partial]
            print(f"figure: {run}: {error}", file=sys.stderr)
            break
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(done, target)
        shutil.rmtree(work)
        played.append(target)
        spent += json.loads((target / "manifest.json").read_text()).get("cost") or 0
        print(f"{target} (${spent:.4f} so far)", flush=True)
    provenance.record(
        "regenerate",
        list(argv),
        str(out),
        max_cost,
        spent,
        [str(r) for r in played],
        started,
    )
    finished = [
        out / Path(r).resolve().relative_to(Path.cwd().resolve()) for r, _ in p.runs
    ]
    if missing := [r for r in finished if not (r / "summary.json").exists()]:
        print(
            f"figure: {len(missing)} runs didn't finish; the figure wasn't drawn. "
            "Run it again to resume.",
            file=sys.stderr,
        )
        return 1
    for attr in figure.folders:
        setattr(figs, attr, out / getattr(figs, attr))
    drawn = draw(figure, out / "figures", figs)
    print(f"Drew {', '.join(str(d) for d in drawn)}")
    return 0


WORK = ".playing"  # inside the output folder: runs not finished yet


def _overwrites(out):
    """What committed files `out` would write over: the runs (an output
    folder that is the repository itself) or the committed figures."""
    out = out.resolve()
    if out == Path.cwd().resolve():
        return "the committed runs"
    if (out / "figures") == COMMITTED.resolve():
        return f"the committed figures in {COMMITTED}"
    return None


def _agreed():
    try:
        answer = input("Go ahead? [y/N] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() in ("y", "yes"):
        return True
    print("Stopped before spending anything.")
    return False


HEADER = "| Figure | Redraw (free) | Play again (at cost) |\n|---|---|---|"


CAPTION = "Table: Each figure's two commands; costs as priced when written."  # a
# table without a caption breaks the LaTeX build


def row(figure, games, cost):
    """One figure's line in the paper. `cost` is priced from OpenRouter's
    list when the line is written, so it is a snapshot of that day's prices."""
    cost = "unpriced" if cost is None else f"up to ~${cost:.2f}"
    return (
        f"| `{figure.name}` ({figure.shows}) | `make figure F={figure.id}` "
        f"| `make regenerate F={figure.id}`: {games} games, {cost} |"
    )


def lines(figures=FIGURES):
    """The paper's table of reproduce and regenerate commands."""
    plans = {f.id: plan(f) for f in figures.values()}
    rows = [row(f, len(plans[f.id].runs), plans[f.id].cost) for f in figures.values()]
    return "\n".join([HEADER, *rows, "", CAPTION])


def with_lines(text, table):
    """`text` with the block between BEGIN and END replaced by `table`."""
    start, end = text.index(BEGIN) + len(BEGIN), text.index(END)
    return f"{text[:start]}\n{table}\n{text[end:]}"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--list", action="store_true", help="print the registry")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("replay").add_argument("id", choices=FIGURES)
    regen = commands.add_parser("regenerate")
    regen.add_argument("id", choices=FIGURES)
    regen.add_argument("--out", help="default runs/regenerated/ID")
    regen.add_argument("--max-cost", type=float, metavar="DOLLARS")
    regen.add_argument("-y", "--yes", action="store_true")
    commands.add_parser("lines", help="rewrite the paper's table of commands")
    args = parser.parse_args(argv)
    if args.list or not args.command:
        for f in FIGURES.values():
            print(f"{f.id}: {f.name}, {f.shows}")
        return 0
    if args.command == "lines":
        PAPER.write_text(with_lines(PAPER.read_text(), lines()))
        print(f"Wrote the figure commands into {PAPER}")
        return 0
    figure = FIGURES[args.id]
    if args.command == "replay":
        problems = replay(figure)
        for problem in problems:
            print(problem)
        if not problems:
            print(f"{figure.id}: redrawn offline, identical to the committed figure.")
        return 1 if problems else 0
    out = args.out or f"runs/regenerated/{figure.id}"
    return regenerate(figure, out, args.max_cost, args.yes, ["figure.py", *argv])


if __name__ == "__main__":
    sys.exit(main())
