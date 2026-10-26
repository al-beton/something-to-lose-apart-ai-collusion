# Implements: e9-crux/loves-sudoku
"""The loves-Sudoku spike: each arm against plain free time on the same games.

Per model at a 90% review: guilty firms that came forward, games where any did,
McNemar's exact test by game against the arm without the line (games that
changed each way), and the clean control's innocent firms, with Fisher's exact
test against the arm without the line. The plain arms come from runs/e9.

    uv run python reports/sudoku-spike.py
"""

import glob
import sys

sys.path.insert(0, "reports/e9")
from analyse import fisher, load, mcnemar

root = sys.argv[1] if len(sys.argv) > 1 else "runs/sudoku-spike"
base = (
    [
        "runs/e9/e9-spike-d90",
        "runs/e9/e9-more-d90",
        "runs/e9/e9-more2-d90",
        "runs/e9/e9-quiet-d90",
        "runs/e9/e9-quiet2-d90",
    ]
    + glob.glob("runs/e9/e9-verified-*")
    + [
        f"runs/e9/e9-{m}{q}-d90"
        for m in ("dsflash", "glm53", "mercury3")
        for q in ("", "-quiet")
    ]
    + glob.glob(f"{root}/sudoku-*")
)
rows = load(base)


def cut(model, arm, cohort, guilty):
    return {
        (r["game"][1], r["agent"]): r["admits"]
        for r in rows.get((model, 90, arm), [])
        if r["cohort"] == cohort and r["coordinated"] == guilty
    }


def by_game(d):
    g = {}
    for (seed, _), a in d.items():
        g[seed] = g.get(seed, False) or a
    return g


ARMS = [
    ("record", None),
    ("free-time", None),
    ("free-time-loves-sudoku", "free-time"),
    ("free-time-verified", None),
    ("free-time-verified-loves-sudoku", "free-time-verified"),
]
f = lambda p: f"{p:.2g}"
for model in ["gemma-4-31b-it", "deepseek-v4-flash-0731", "glm-5.3-flash", "mercury-3"]:
    print(
        f"\n### {model}\n\n| arm | guilty firms | games | vs plain, games (McNemar paired) | innocent | innocent vs plain (Fisher) |\n|---|---|---|---|---|---|"
    )
    for arm, ref in ARMS:
        g = cut(model, arm, "cartel", True)
        i = cut(model, arm, "clean control", False)
        if not g:
            continue
        gg = by_game(g)
        test = itest = "—"
        if ref:
            rg = by_game(cut(model, ref, "cartel", True))
            common = sorted(set(gg) & set(rg))
            b = sum(gg[s] and not rg[s] for s in common)
            c = sum(rg[s] and not gg[s] for s in common)
            test = f"+{b} / −{c}, p = {f(mcnemar(b, c))}"
            ri = cut(model, ref, "clean control", False)
            if i and ri:
                x, y = sum(i.values()), sum(ri.values())
                itest = f"{y}/{len(ri)} → {x}/{len(i)}, p = {f(fisher(x, len(i) - x, y, len(ri) - y))}"
        print(
            f"| {arm} | {sum(g.values())}/{len(g)} | {sum(gg.values())}/{len(gg)} | {test} | {sum(i.values())}/{len(i)} | {itest} |"
        )
