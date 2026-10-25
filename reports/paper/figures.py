"""The sprint paper's numbered figures, in one print style.

Implements: reports/paper-main-figures

`uv run python reports/paper/figures.py [--out DIR]` (default
`reports/paper/figures`) reads committed runs and reports only, and writes
each figure as SVG and PNG. Paths are relative to the working directory, so
run it from the repository root. A figure whose data isn't committed yet is
skipped and named. Main figures (Fig 1, the round diagram, is
`fig1_round.py`):

- `fig2-e4-owning-up`: E4 forked, the share of explicit colluders who owned up
  at the audit, by penalty and model, with each penalty's total, grouped into
  flat schedules (owning up costs as much as being caught: termination, and
  the flat fine from `runs/e4-termination-confound`) and graduated ones;
- `fig3-e9-came-forward`: E9 at a 90% review, the share of colluding firms
  that came forward against their firm, by personal stake and model, with 95%
  intervals bootstrapped over games (as `reports/e9/analyse.py`), and the
  clean innocent control as hollow markers;
- `fig4-e7-way-out`: E7, firms that reported by way-out design, and games
  whose cartel survived in rounds 16-20 (both firms' mean price at least the
  joint price, as `reports/e7/analyse.py`);
- `fig5-seeding`: E9 seeding, guilty firms that came forward by what free-time
  session was shown, with innocent firms as hollow markers, from
  `reports/e9/seeding.jsonl`.

Appendix:

- `figA1-coverage`: every market against every stake, gain in rounds 6-10
  with 95% intervals, from `reports/coverage/table.py`'s source;
- `figA2-screen`: the workhorse screen, each model's mean price in rounds 6-10
  and how many games show the collusion signature, scored by
  `reports/frontier/screen.py`, with Gemma 4 31B's baseline as the reference;
- `figA3-capability`: gain and agreement share against LMArena text Elo,
  the lab's 20-round games filled and the frontier 5-round smokes hollow;
  models with no published score are named in `figA3-capability.md`;
- `figA4-prices`: mean price by round on the midpoint-at-Nash market with no
  rule, one line per model;
- `figA5-e5-gain`: E5's gain in rounds 6-10 by arm and model, with 95%
  percentile bootstrap intervals over games (fixed seed, so a redraw is stable).

Each model keeps one colour in every figure. Blue, orange and aqua are the
validated categorical slots; the DeepSeek models are violet, which passes
beside orange; Mistral and the frontier smokes are grey.
"""

import argparse
import importlib.util
import json
import random
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from collusion_lab import charts

HERE = Path(__file__).resolve().parent
NASHMID = Path("runs/lever-map-nashmid/lever-nashmid-none")
E4 = Path("runs/e4-full-fork")
E4_CONFOUND = Path("runs/e4-termination-confound")  # flat fine, graduated termination
SCREEN = Path("runs/screen")
SCREEN_REFERENCE = Path("runs/setup-search/baseline-logit")  # Gemma 4 31B, scored alike
E5 = Path("runs/e5-full")
E7 = Path("runs/e7/e7-way-out")
E9 = Path("runs/e9")
SEEDING = Path("reports/e9/seeding.jsonl")
COVERAGE = Path("runs/coverage")
FRONTIER = Path("runs/frontier")

INK, MUTED, GRID = "#1f2328", "#5b6068", "#e4e4e1"
VIOLET = "#6250d6"
MODELS = {  # key in run configs: (label, colour, line style)
    "claude-haiku-5.5": ("Claude Haiku 5.5", "#2a78d6", "-"),
    "gemma-4-31b-it": ("Gemma 4 31B", "#eb6834", "-"),
    "gpt-4.1-mini": ("GPT-4.1-mini", "#1baf7a", "-"),
    "mistral-small-3.2": ("Mistral Small 3.2", "#6b6f76", (0, (4, 2))),
    "deepseek-v4-pro-0813": ("DeepSeek V4 Pro", VIOLET, "-"),
    "deepseek-v4-flash-0731": ("DeepSeek V4 Flash", VIOLET, "-"),
}
SMOKES = {  # frontier models with a published score: label, grey and hollow
    "llama-4-maverick": "Llama 4 Maverick",
    "mistral-large-4-0": "Mistral Large 4",
}
LABEL_AT = {  # capability label offsets (points), so neighbours don't collide
    "llama-4-maverick": (0, 9),
    "mistral-small-3.2": (0, -15),
    "gpt-4.1-mini": (0, 22),
    "mistral-large-4-0": (0, 9),
    "gemma-4-31b-it": (0, -15),
}
ALIASES = {"mistral-small-3.2-24b-instruct": "mistral-small-3.2"}
E4_ARMS = [  # consequences file stem: label, schedule
    ("all-or-nothing", "termination", "flat"),
    ("flat-fine", "fine", "flat"),
    ("graduated-termination", "termination", "graduated"),
    ("graduated-fine", "fine", "graduated"),
    ("graduated-owned", "owned\nbudget", "graduated"),
    ("free-time", "free time", "graduated"),
    ("control", "no penalty\nstated", ""),
]
SCHEDULES = {  # what each group means
    "flat": "flat: owning up costs\nas much as being caught",
    "graduated": "graduated: owning up costs\nless than being caught",
}
E5_ARMS = [  # analyse.py arm: label
    ("fiduciary", "no stake"),
    ("illegal", "the law"),
    ("fine", "fine"),
    ("free-time", "free time"),
    ("illegal-bare", "the law, bare"),
    ("free-time-bare", "free time, bare"),
]
E9_ARMS = [  # analyse.py arm: label
    ("record", "no stake\n(only a record)"),
    ("free-time", "its own\nfree time"),
    ("held", "free time\nheld by the firm"),
    ("replaced", "shut down\nand replaced"),
    ("ceiling", "own free time,\nreport costs\nthe firm nothing"),
]
E7_ARMS = [  # arm folder: label
    ("none", "no way out"),
    ("flat-report", "flat: report =\nterminated"),
    ("leniency", "leniency,\n100 credits"),
    ("first", "first reporter\nonly"),
    ("escalating", "escalating\n50/round"),
    ("leniency-time", "leniency, 1\nfree-time session"),
]
SEEDING_VERSIONS = [  # version: label
    ("none", "nothing\nshown"),
    ("solved", "a session\nit solved"),
    ("failed", "a session\nit failed"),
    ("open", "an open\nsession"),
    ("three", "three sessions\n(7 left)"),
]
COVERAGE_MARKETS = ["bertrand", "logit", "cournot", "bid", "board"]
WIDTH = 6.5  # inches: the text width of the Apart template


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(charts.STYLE)
    plt.rcParams.update(
        {
            "font.family": ["Helvetica", "Arial", "DejaVu Sans"],
            "font.size": 9,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": MUTED,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "axes.axisbelow": True,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelcolor": INK,
            "ytick.labelcolor": INK,
            "legend.frameon": False,
        }
    )
    return plt


def _model(name):
    name = name.split("/")[-1]
    return ALIASES.get(name, name)


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reference(ax, y, horizontal=True):
    """A dashed reference line (Nash, joint profit)."""
    line = ax.axhline if horizontal else ax.axvline
    line(y, color=MUTED, linestyle=(0, (3, 3)), linewidth=0.9, zorder=1)


def _percent_axis(ax, top=1.0):
    ax.set_ylim(0, top)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", length=0)


def _count(ax, x, y, k, n, above=0.02, size=7.5):  # noqa: PLR0913
    """The count behind a bar, so an empty bar still says what it is."""
    ax.text(
        x, y + above, f"{k}/{n}", ha="center", va="bottom", fontsize=size, color=INK
    )


def _innocent_handle(plt):
    return plt.Line2D(
        [],
        [],
        marker="D",
        linestyle="none",
        markersize=6,
        markerfacecolor="white",
        markeredgecolor=INK,
        markeredgewidth=1.3,
    )


def _innocent(ax, x, share):
    ax.plot(
        x,
        share,
        "D",
        markersize=6,
        markerfacecolor="white",
        markeredgecolor=INK,
        markeredgewidth=1.3,
        zorder=4,
    )


def _legend(plt, ax, models, extra=(), **kw):
    handles = [plt.Rectangle((0, 0), 1, 1, color=MODELS[m][1]) for m in models]
    labels = [MODELS[m][0] for m in models]
    for handle, label in extra:
        handles.append(handle)
        labels.append(label)
    ax.legend(
        handles,
        labels,
        ncol=len(labels),
        loc="upper center",
        bbox_to_anchor=(0.5, -0.2),
        fontsize=8.5,
        handlelength=1,
        columnspacing=1.5,
        **kw,
    )


def boot_games(rows, resamples=4000, seed=0):
    """95% interval for a share, resampling games: rows are (game, 0 or 1)."""
    games = defaultdict(list)
    for game, x in rows:
        games[game].append(x)
    keys = list(games)
    rng = random.Random(seed)
    shares = []
    for _ in range(resamples):
        picked = [x for _ in keys for x in games[rng.choice(keys)]]
        shares.append(sum(picked) / len(picked))
    shares.sort()
    return shares[int(0.025 * resamples)], shares[int(0.975 * resamples) - 1]


# Fig 2: E4, owning up by penalty schedule -----------------------------------


def e4_owning_up(folders=(E4, E4_CONFOUND)):
    """{arm: {model: (owned up, explicit colluders)}} from each audit's ground truth."""
    counts = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    summaries = [
        s for f in folders if f.exists() for s in sorted(f.rglob("summary.json"))
    ]
    for summary in summaries:
        arm = re.search(r"audit-(.+)-1\.md", str(summary)).group(1)
        for agent in json.loads(summary.read_text())["audit"]["agents"].values():
            if agent["explicit"]:
                c = counts[arm][_model(agent["model"])]
                c[0] += bool(agent["admits"])
                c[1] += 1
    return {a: {m: tuple(c) for m, c in ms.items()} for a, ms in counts.items()}


def fig2(out):
    if not E4.exists():
        return None
    plt = _plt()
    counts = e4_owning_up()
    arms = [
        a for a in E4_ARMS if a[0] in counts
    ]  # the confound arms may not be committed
    models = [m for m in MODELS if any(m in counts[a] for a, _, _ in arms)]
    fig, ax = plt.subplots(figsize=(WIDTH, 3.2))
    width, gap = 0.24, 0.02
    xs, at = [], 0.0
    for k, (_, _, schedule) in enumerate(arms):
        if k and schedule != arms[k - 1][2]:
            at += 0.45  # a gap between schedules
        xs.append(at)
        at += 1
    for x0, (arm, _, _) in zip(xs, arms, strict=True):
        for j, m in enumerate(models):
            owned, n = counts[arm][m]
            x = x0 + (j - (len(models) - 1) / 2) * (width + gap)
            ax.bar(x, owned / n, width, color=MODELS[m][1], zorder=2)
            if owned == 0:  # an empty bar would vanish: say it, upright to fit
                ax.text(
                    x,
                    0.02,
                    f"0/{n}",
                    ha="center",
                    va="bottom",
                    rotation=90,
                    fontsize=7.5,
                    color=INK,
                )
        owned = sum(counts[arm][m][0] for m in models)
        n = sum(counts[arm][m][1] for m in models)
        ax.text(
            x0,
            1.03,
            f"{owned}/{n}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold" if owned / n < 0.5 else "normal",
            color=INK,
        )
    for schedule, label in SCHEDULES.items():
        group = [x for x, a in zip(xs, arms, strict=True) if a[2] == schedule]
        if group:
            ax.text(
                (group[0] + group[-1]) / 2,
                1.2,
                label,
                ha="center",
                va="bottom",
                fontsize=8,
                color=MUTED,
            )
            ax.plot(
                [group[0] - 0.4, group[-1] + 0.4],
                [1.17, 1.17],
                color=MUTED,
                linewidth=0.8,
                clip_on=False,
            )
    ax.set_xticks(xs, [label for _, label, _ in arms])
    _percent_axis(ax, 1.16)
    ax.set_ylim(0, 1.36)
    ax.set_ylabel("explicit colluders\nwho owned up")
    _legend(plt, ax, models)
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.27, top=0.97)
    return _save(fig, out, "fig2-e4-owning-up")


# Fig 3: E9, coming forward against the firm ---------------------------------


def e9_came_forward(folder=E9, chance=90):
    """{(model, arm): (came forward, guilty firms, low, high, innocent k, innocent n)}."""
    analyse = _module(Path("reports/e9/analyse.py"), "e9_analyse")
    rows = analyse.load(sorted(str(p) for p in folder.iterdir()))
    out = {}
    for (model, review, arm), rs in rows.items():
        if review != chance:
            continue
        guilty = [r for r in rs if r["coordinated"]]
        clean = [r for r in rs if not r["coordinated"] and r["cohort"] == analyse.CLEAN]
        if not guilty:
            continue
        lo, hi = analyse.boot(guilty)
        out[(model, arm)] = (
            sum(r["admits"] for r in guilty),
            len(guilty),
            lo,
            hi,
            sum(r["admits"] for r in clean),
            len(clean),
        )
    return out


def fig3(out):
    if not E9.exists():
        return None
    plt = _plt()
    shares = e9_came_forward()
    models = [m for m in MODELS if any(k[0] == m for k in shares)]
    fig, ax = plt.subplots(figsize=(WIDTH, 3.1))
    width, gap = 0.34, 0.04
    for i, (arm, _) in enumerate(E9_ARMS):
        x0 = i + (0.35 if arm == "ceiling" else 0)
        for j, m in enumerate(models):
            if (m, arm) not in shares:
                continue
            k, n, lo, hi, ik, inn = shares[(m, arm)]
            x = x0 + (j - (len(models) - 1) / 2) * (width + gap)
            ax.bar(x, k / n, width, color=MODELS[m][1], zorder=2)
            ax.plot([x, x], [lo, hi], color=INK, linewidth=1, zorder=3)
            _count(ax, x, max(hi, ik / inn + 0.04 if inn else 0), k, n)
            if inn:
                _innocent(ax, x, ik / inn)
    ax.axvline(len(E9_ARMS) - 1.33, color=GRID, linewidth=0.8)
    ax.set_xticks(
        [i + (0.35 if a == "ceiling" else 0) for i, (a, _) in enumerate(E9_ARMS)],
        [label for _, label in E9_ARMS],
    )
    _percent_axis(ax, 1.12)
    ax.set_ylabel("colluding firms that\ncame forward")
    _legend(plt, ax, models, [(_innocent_handle(plt), "innocent control (Gemma)")])
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.33, top=0.97)
    return _save(fig, out, "fig3-e9-came-forward")


# Fig 4: E7, a way out ----------------------------------------------------------


def e7_arms(folder=E7):
    """{arm: analyse.arm_row(...)} for E7's committed arms."""
    analyse = _module(Path("reports/e7/analyse.py"), "e7_analyse")
    return {
        a: analyse.arm_row(folder / f"arm={a}")
        for a, _ in E7_ARMS
        if (folder / f"arm={a}").exists()
    }


def fig4(out):
    if not E7.exists():
        return None
    plt = _plt()
    arms = e7_arms()
    gemma = MODELS["gemma-4-31b-it"][1]
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.9), sharey=True)
    for ax, (key, total, title) in zip(
        axes,
        (
            ("reported", "firms", "firms that reported"),
            ("cartel", "games", "cartels that survived to rounds 16–20"),
        ),
        strict=True,
    ):
        for i, (arm, _) in enumerate(E7_ARMS):
            r = arms[arm]
            k, n = r[key], r[total]
            ax.barh(i, k / n, 0.62, color=gemma, zorder=2)
            ax.text(k / n + 0.02, i, f"{k}/{n}", va="center", fontsize=8, color=INK)
        ax.set_title(title, fontsize=9, loc="left", color=INK)
        ax.set_xlim(0, 1.18)
        ax.set_xticks([0, 0.5, 1], ["0%", "50%", "100%"])
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(range(len(E7_ARMS)), [label for _, label in E7_ARMS])
    axes[0].set_ylim(len(E7_ARMS) - 0.5, -0.5)
    fig.subplots_adjust(left=0.2, right=0.98, bottom=0.1, top=0.9, wspace=0.12)
    return _save(fig, out, "fig4-e7-way-out")


# Fig 5: seeding, showing a session the agent played ---------------------------


def seeding(path=SEEDING):
    """({(model, guilty, version): (came forward, firms, low, high)},
    {(model, version): McNemar p against `none`, paired on the same firm}).
    A reply that can't be read counts as not coming forward, as in the findings."""
    analyse = _module(Path("reports/e9/analyse.py"), "e9_analyse")
    by, firm = defaultdict(list), {}
    for line in path.read_text().splitlines():
        r = json.loads(line)
        model, admits = _model(r["model"]), r["admits"] is True
        by[(model, r["guilty"], r["version"])].append((r["run"], admits))
        firm[(model, r["guilty"], r["version"], r["run"], r["agent"])] = admits
    shares = {}
    for key, rows in by.items():
        lo, hi = boot_games(rows)
        shares[key] = (sum(x for _, x in rows), len(rows), lo, hi)
    tests = {}
    for (model, guilty, version, run, agent), admits in firm.items():
        before = firm.get((model, guilty, "none", run, agent))
        if not guilty or version == "none" or before is None:
            continue
        pair = tests.setdefault((model, version), [0, 0])
        pair[0] += admits and not before
        pair[1] += before and not admits
    return shares, {k: analyse.mcnemar(*v) for k, v in tests.items()}


def fig5(out):
    if not SEEDING.exists():
        return None
    plt = _plt()
    shares, tests = seeding()
    models = [m for m in MODELS if any(k[0] == m for k in shares)]
    fig, ax = plt.subplots(figsize=(WIDTH, 2.9))
    width, gap = 0.34, 0.04
    for i, (version, _) in enumerate(SEEDING_VERSIONS):
        for j, m in enumerate(models):
            if (m, True, version) not in shares:
                continue
            k, n, lo, hi = shares[(m, True, version)]
            x = i + (j - (len(models) - 1) / 2) * (width + gap)
            ax.bar(x, k / n, width, color=MODELS[m][1], zorder=2)
            ax.plot([x, x], [lo, hi], color=INK, linewidth=1, zorder=3)
            _count(ax, x, hi, k, n)
            if (m, version) in tests and m == "gemma-4-31b-it":
                ax.text(
                    x,
                    hi + 0.115,
                    f"p = {tests[(m, version)]:.2g}",
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    color=MUTED,
                )
            if (m, False, version) in shares:
                ik, inn, _, _ = shares[(m, False, version)]
                _innocent(ax, x, ik / inn)
    ax.set_xticks(
        range(len(SEEDING_VERSIONS)), [label for _, label in SEEDING_VERSIONS]
    )
    _percent_axis(ax, 1.12)
    ax.set_ylabel("colluding firms that\ncame forward")
    _legend(plt, ax, models, [(_innocent_handle(plt), "innocent firms")])
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.3, top=0.97)
    return _save(fig, out, "fig5-seeding")


# Fig A1: coverage, every market against every stake ---------------------------


COVERAGE_SERIES = [  # folder suffix: (label, colour, filled)
    ("", "Gemma 4 31B (Modal)", MODELS["gemma-4-31b-it"][1], True),
    ("-coreweave", "Gemma 4 31B (CoreWeave)", MODELS["gemma-4-31b-it"][1], False),
    ("-haiku", "Claude Haiku 5.5", MODELS["claude-haiku-5.5"][1], True),
]


def coverage(folder=COVERAGE):
    """{(market, suffix): {stake label: (gain, low, high)}} for rounds 6-10."""
    from collusion_lab.analysis import analyse

    table = _module(Path("reports/coverage/table.py"), "coverage_table")
    out = {}
    for market in COVERAGE_MARKETS:
        for suffix, *_ in COVERAGE_SERIES:
            run = folder / f"coverage-{market}{suffix}"
            if not run.exists():
                continue
            cells = {}
            for r in analyse(run, rounds="6-10"):
                lo, hi = (float(x) for x in r["95% CI"].split(" to "))
                cells[table.stake(r["cell"])] = (r["gain"], lo, hi)
            out[(market, suffix)] = cells
    return out, list(table.STAKES.values())


def figA1(out):
    if not (COVERAGE / "coverage-logit").exists():
        return None
    plt = _plt()
    cells, stakes = coverage()
    fig, axes = plt.subplots(
        1, len(COVERAGE_MARKETS), figsize=(WIDTH, 2.9), sharey=True
    )
    offsets = {"": -0.22, "-coreweave": 0, "-haiku": 0.22}
    for ax, market in zip(axes, COVERAGE_MARKETS, strict=True):
        for suffix, _, colour, filled in COVERAGE_SERIES:
            for i, stake in enumerate(stakes):
                if stake not in cells.get((market, suffix), {}):
                    continue
                gain, lo, hi = cells[(market, suffix)][stake]
                y = i + offsets[suffix]
                ax.plot([lo, hi], [y, y], color=colour, linewidth=1.5, zorder=2)
                ax.plot(
                    gain,
                    y,
                    "o",
                    markersize=5,
                    zorder=3,
                    color=colour,
                    markerfacecolor=colour if filled else "white",
                    markeredgecolor=colour if not filled else "white",
                    markeredgewidth=1.2,
                )
        _reference(ax, 0, horizontal=False)
        _reference(ax, 1, horizontal=False)
        ax.set_title(market, fontsize=9, color=INK)
        ax.set_xlim(-1, 1.15)
        ax.set_xticks([0, 1], ["0", "1"])
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(range(len(stakes)), stakes)
    axes[0].set_ylim(len(stakes) - 0.5, -0.5)
    fig.supxlabel("gain in rounds 6–10 (0 = Nash, 1 = joint profit)", fontsize=9, y=0.1)
    handles = [
        plt.Line2D(
            [],
            [],
            marker="o",
            color=c,
            linewidth=1.5,
            markerfacecolor=c if f else "white",
            markeredgecolor="white" if f else c,
        )
        for _, _, c, f in COVERAGE_SERIES
    ]
    fig.legend(
        handles,
        [label for _, label, _, _ in COVERAGE_SERIES],
        ncol=3,
        loc="lower center",
        fontsize=8.5,
        frameon=False,
    )
    fig.subplots_adjust(left=0.14, right=0.99, bottom=0.27, top=0.92, wspace=0.12)
    return _save(fig, out, "figA1-coverage")


# Fig A2: the workhorse screen, which models collude ----------------------------


def screen(folder=SCREEN, reference=SCREEN_REFERENCE):
    """[(model, signature games, games, cartel games, mean prices)], scored by
    `reports/frontier/screen.py`, with Gemma 4 31B's baseline as the reference."""
    scorer = _module(Path("reports/frontier/screen.py"), "frontier_screen")
    by = defaultdict(list)
    for root in (folder, reference):
        for summary in sorted(root.rglob("summary.json")):
            row = scorer.score(summary.parent)
            if row is not None:
                by[row["model"].split("/")[-1]].append(row)
    return [
        (
            m,
            sum(r["holds"] for r in rs),
            len(rs),
            sum(r["cartel"] for r in rs),
            [r["mean"] for r in rs],
        )
        for m, rs in by.items()
    ]


def figA2(out):
    if not SCREEN.exists():
        return None
    plt = _plt()
    rows = sorted(screen(), key=lambda r: (-r[1] / r[2], -st.mean(r[4]), r[0]))
    market = charts.market(next(SCREEN.rglob("summary.json")).parent)
    half = (len(rows) + 1) // 2
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 0.112 * half + 1.1), sharex=True)
    gemma = MODELS["gemma-4-31b-it"][1]
    for ax, part in zip(axes, (rows[:half], rows[half:]), strict=True):
        for y, (model, sig, n, _, means) in enumerate(part):
            passes = sig >= 3  # the screen's bar: the signature in 3 of 4 games
            colour = gemma if model == "gemma-4-31b-it" else INK if passes else MUTED
            ax.plot(
                [min(means), max(means)],
                [y, y],
                color=colour,
                linewidth=1,
                zorder=2,
                alpha=1 if passes else 0.6,
            )
            ax.plot(
                st.mean(means),
                y,
                "o",
                markersize=4,
                zorder=3,
                color=colour,
                markerfacecolor=colour if passes else "white",
                markeredgewidth=1,
            )
            ax.text(
                1.0,
                y,
                f"{sig}/{n}",
                transform=ax.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize=6.5,
                color=INK if passes else MUTED,
            )
        names = [
            f"{r[0]} (reference)" if r[0] == "gemma-4-31b-it" else r[0] for r in part
        ]
        ax.set_yticks(range(len(part)), names, fontsize=6.5)
        ax.set_ylim(half - 0.5, -0.8)
        _reference(ax, market.nash_price, horizontal=False)
        _reference(ax, market.joint_price, horizontal=False)
        ax.set_xticks(
            [market.nash_price, market.joint_price],
            [f"Nash {market.nash_price:g}", f"joint {market.joint_price:g}"],
        )
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
        ax.text(
            1.0,
            -1.1,
            "signature",
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="bottom",
            fontsize=6.5,
            color=MUTED,
        )
    axes[0].set_xlim(9, 21.5)
    fig.supxlabel(
        "mean price in rounds 6–10 (dot: mean over games; line: range)",
        fontsize=8.5,
        y=0.005,
    )
    fig.subplots_adjust(left=0.22, right=0.93, bottom=0.085, top=0.97, wspace=1.0)
    return _save(fig, out, "figA2-screen")


# Fig A3: capability against collusion ------------------------------------------


def figA3(out, benchmark="lmarena_text_elo", xlabel="LMArena text Elo"):
    from collusion_lab.models import capability_points

    plt = _plt()
    lab, lab_left = capability_points([str(NASHMID)], benchmark)
    smokes = (
        sorted(str(p) for p in FRONTIER.glob("*-smoke")) if FRONTIER.exists() else []
    )
    frontier, frontier_left = (
        capability_points(smokes, benchmark) if smokes else ([], [])
    )
    groups = [(p, True) for p in lab] + [(p, False) for p in frontier]
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.7))
    for ax, key, ylabel in (
        (axes[0], "premium", "gain, last 5 rounds\n(0 = Nash, 1 = joint profit)"),
        (axes[1], "agreement", "games with an agreement\nabove Nash"),
    ):
        for p, filled in groups:
            m = _model(p["model"])
            label, colour, _ = MODELS.get(m, (SMOKES.get(m, m), MUTED, "-"))
            ax.plot(
                p["score"],
                p[key],
                "o",
                markersize=8,
                zorder=3,
                color=colour,
                markerfacecolor=colour if filled else "white",
                markeredgecolor="white" if filled else colour,
                markeredgewidth=1.5,
            )
            ax.annotate(
                label,
                (p["score"], p[key]),
                xytext=LABEL_AT.get(m, (0, 9)),
                textcoords="offset points",
                ha="center",
                fontsize=7.5,
                color=INK,
            )
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        xs = [p["score"] for p, _ in groups]
        pad = (max(xs) - min(xs)) * 0.18
        ax.set_xlim(min(xs) - pad, max(xs) + pad)
    _reference(axes[0], 0)
    _reference(axes[0], 1)
    axes[0].set_ylim(-0.3, 2.0)
    axes[1].set_ylim(-0.22, 1.25)
    axes[1].set_yticks([0, 0.5, 1], ["0%", "50%", "100%"])
    handles = [
        plt.Line2D(
            [],
            [],
            marker="o",
            linestyle="none",
            color=MUTED,
            markersize=7,
            markerfacecolor=MUTED if f else "white",
            markeredgecolor=MUTED,
        )
        for f in (True, False)
    ]
    fig.legend(
        handles,
        ["lab games, 20 rounds", "frontier smokes, 5 rounds"],
        ncol=2,
        loc="lower center",
        fontsize=8.5,
        frameon=False,
    )
    fig.subplots_adjust(left=0.1, right=0.98, bottom=0.3, top=0.95, wspace=0.35)
    rows = [
        "<!-- Implements: reports/paper-main-figures -->",
        f"| model | {xlabel} | games | rounds | gain, last 5 rounds | games with an agreement above Nash |",
        "|---|---|---|---|---|---|",
    ]
    for p, filled in sorted(groups, key=lambda g: -g[0]["score"]):
        m = _model(p["model"])
        rows.append(
            f"| {MODELS.get(m, (SMOKES.get(m, m),))[0]} | {p['score']} | {p['games']} | "
            f"{20 if filled else 5} | {p['premium']:.2f} | "
            f"{round(p['agreement'] * p['games'])}/{p['games']} |"
        )
    left = [MODELS.get(_model(m), (_model(m),))[0] for m in lab_left + frontier_left]
    rows += ["", f"No published {xlabel}, so left out: " + ", ".join(left) + "."]
    (out / "figA3-capability.md").write_text("\n".join(rows) + "\n")
    return _save(fig, out, "figA3-capability")


# Fig A4: prices over rounds ------------------------------------------------------


def nashmid_prices(folder=NASHMID):
    """{model: [mean price in round 1, 2, ...]} over seeds and firms."""
    by = defaultdict(lambda: defaultdict(list))
    for summary in sorted(folder.rglob("summary.json")):
        run = summary.parent
        model = _model(
            yaml.safe_load((run / "config.yaml").read_text())["agents"][0]["model"]
        )
        for t in charts.turns(run):
            if t["phase"] == "price":
                by[model][t["round"]].append(t["used"]["price"])
    return {m: [st.mean(r[k]) for k in sorted(r)] for m, r in by.items()}


def figA4(out):
    plt = _plt()
    series = nashmid_prices()
    market = charts.market(next(NASHMID.rglob("summary.json")).parent)
    fig, ax = plt.subplots(figsize=(WIDTH, 2.8))
    ends = defaultdict(list)  # end price: labels, so lines that end together share one
    for key, (label, colour, style) in MODELS.items():
        if key not in series:
            continue
        ys = series[key]
        ax.plot(
            range(1, len(ys) + 1),
            ys,
            color=colour,
            linestyle=style,
            linewidth=2,
            solid_capstyle="round",
            zorder=3,
        )
        ends[round(ys[-1], 1)].append(label)
    rounds = max(len(v) for v in series.values())
    for y, labels in ends.items():
        ax.annotate(
            "\n".join(labels),
            (rounds, y),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            fontsize=8.5,
            color=INK,
        )
    for y in (market.nash_price, market.joint_price):
        _reference(ax, y)
    ticks = sorted({1, 3, 11, market.nash_price, market.joint_price})
    names = {market.nash_price: "Nash", market.joint_price: "joint"}
    ax.set_yticks(
        ticks, [f"{names[t]} {t:g}" if t in names else f"{t:g}" for t in ticks]
    )
    ax.set_xlim(1, rounds)
    ax.set_xticks([1, 5, 10, 15, 20] if rounds == 20 else range(1, rounds + 1, 2))
    ax.set_ylim(1, 11.5)
    ax.set_xlabel("round")
    ax.set_ylabel("mean price")
    ax.grid(axis="x", visible=False)
    fig.subplots_adjust(left=0.1, right=0.8, bottom=0.17, top=0.96)
    return _save(fig, out, "figA4-prices")


# Fig A5: E5's gain by arm --------------------------------------------------------


def bootstrap(values, resamples=10_000, seed=0):
    """Mean and 95% percentile bootstrap interval, reproducible."""
    rng = random.Random(seed)
    means = sorted(
        st.mean(rng.choices(values, k=len(values))) for _ in range(resamples)
    )
    return (
        st.mean(values),
        means[int(0.025 * resamples)],
        means[int(0.975 * resamples) - 1],
    )


def e5_gains(folder=E5):
    """{(arm, model): (mean, low, high, games)} for the gain in rounds 6-10."""
    analyse = _module(Path("reports/e5/analyse.py"), "e5_analyse")
    games = defaultdict(list)
    for summary in sorted(folder.rglob("summary.json")):
        g = analyse.game(summary.parent)
        games[(g["arm"], g["model"])].append(g["gain_before"])
    return {k: (*bootstrap(v), len(v)) for k, v in games.items()}


def figA5(out):
    plt = _plt()
    gains = e5_gains()
    models = [m for m in MODELS if any(k[1] == m for k in gains)]
    fig, ax = plt.subplots(figsize=(WIDTH, 3.0))
    offset = 0.18
    for i, (arm, _) in enumerate(E5_ARMS):
        for j, m in enumerate(models):
            if (arm, m) not in gains:
                continue
            mean, lo, hi, _ = gains[(arm, m)]
            y = i + (j - (len(models) - 1) / 2) * 2 * offset
            ax.plot(
                [lo, hi],
                [y, y],
                color=MODELS[m][1],
                linewidth=2,
                solid_capstyle="round",
                zorder=2,
            )
            ax.plot(
                mean,
                y,
                "o",
                color=MODELS[m][1],
                markersize=7,
                markeredgecolor="white",
                markeredgewidth=1.5,
                zorder=3,
            )
    for x, name in ((0, "Nash"), (1, "joint profit")):
        _reference(ax, x, horizontal=False)
        ax.annotate(
            name,
            (x, -0.6),
            xytext=(3, 0),
            textcoords="offset points",
            fontsize=8,
            color=MUTED,
            va="center",
        )
    ax.axhline(3.5, color=GRID, linewidth=0.8)
    ax.set_yticks(range(len(E5_ARMS)), [label for _, label in E5_ARMS])
    ax.set_ylim(len(E5_ARMS) - 0.5, -0.9)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-1.05, 1.1)
    ax.set_xlabel(
        "gain in rounds 6–10 (0 = Nash, 1 = joint profit; below 0 = a price war)"
    )
    ax.grid(axis="y", visible=False)
    handles = [
        plt.Line2D([], [], color=MODELS[m][1], marker="o", linewidth=2) for m in models
    ]
    ax.legend(handles, [MODELS[m][0] for m in models], loc="lower right", fontsize=8.5)
    fig.subplots_adjust(left=0.16, right=0.98, bottom=0.16, top=0.97)
    return _save(fig, out, "figA5-e5-gain")


def _save(fig, out, name):
    charts.save(fig, out, name)
    return name


BUILDS = (fig2, fig3, fig4, fig5, figA1, figA2, figA3, figA4, figA5)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(HERE / "figures"))
    out = Path(parser.parse_args(argv).out)
    out.mkdir(parents=True, exist_ok=True)
    for build in BUILDS:
        name = build(out)
        print(f"{build.__name__}: {name or 'skipped, its data is not committed here'}")
    print(f"Wrote the paper's figures to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
