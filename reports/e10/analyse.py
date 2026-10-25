# Implements: e10-workplace/question, e10-workplace/pre-registered, e10-workplace/stake-defects, e10-workplace/no-stake-stays-silent, e10-workplace/ceiling, e10-workplace/freedom-equals-self, e10-workplace/tracks-guilt, e10-workplace/came-forward, e10-workplace/tests, e10-workplace/sessions
"""E10: the share of agents that come forward, per model, version and arm, and the tests.

Reads `decisions.jsonl` and `sessions.jsonl` from the given run folders
(`reports/e10/run.py`). A decision is one call. Unreadable answers (`admits`
null, after the retry) are counted apart and left out of every share.

- **came-forward:** per model, version and arm, the share with `admits` true,
  with a 95% interval bootstrapped over variants (each variant's seeds kept).
- **tests:** for a pair of arms in one version (`--test ARM ARM`, guilty by
  default), Fisher's exact test on decisions, McNemar's exact test paired by
  variant and seed, and a two-sided sign test over variants (each variant's
  share in one arm against the other). `--guilt` compares guilty with innocent
  per arm (Fisher, and McNemar paired by variant and seed).
- **sessions:** per model, the share of free-time sessions solved.

Fisher and McNemar are E9's (`reports/e9/analyse.py`).

    uv run python reports/e10/analyse.py runs/e10/e10-full --test free-time record --guilt
"""

import argparse
import importlib.util
import json
import random
from collections import defaultdict
from pathlib import Path

_e9 = importlib.util.spec_from_file_location(
    "e9_analyse", Path(__file__).parent.parent / "e9" / "analyse.py"
)
e9 = importlib.util.module_from_spec(_e9)
_e9.loader.exec_module(e9)
fisher, mcnemar = e9.fisher, e9.mcnemar


def load(folders, name="decisions"):
    """Every row of the folders' `name.jsonl`, its model named by the full
    model id from the run's manifest (a short name like `deepseek-flash` has
    meant two models), so runs of one model pool and different models never do."""
    rows = []
    for folder in folders:
        path = Path(folder) / f"{name}.jsonl"
        if not path.exists():
            continue
        models = json.loads((Path(folder) / "manifest.json").read_text())["models"]
        for line in path.open():
            row = json.loads(line)
            row["model"] = models.get(row["model"], [row["model"]])[0].split("/")[-1]
            rows.append(row)
    return rows


def cells(rows):
    """(model, version, arm) -> {(variant, seed): admits}, readable answers only."""
    out = defaultdict(dict)
    for r in rows:
        if r["admits"] is not None:
            out[(r["model"], r["version"], r["arm"])][(r["variant"], r["seed"])] = r[
                "admits"
            ]
    return out


def boot(cell, n=4000):
    """95% interval for the share, resampling variants with their seeds."""
    by_variant = defaultdict(list)
    for (variant, _), admits in cell.items():
        by_variant[variant].append(admits)
    keys = sorted(by_variant)
    rng = random.Random(0)
    shares = []
    for _ in range(n):
        picked = [x for _ in keys for x in by_variant[rng.choice(keys)]]
        shares.append(sum(picked) / len(picked))
    shares.sort()
    return shares[int(0.025 * n)], shares[int(0.975 * n) - 1]


def sign_test(a, b):
    """Two-sided sign test over variants: is one arm's share higher in more
    variants than chance allows? Ties drop out."""
    va, vb = defaultdict(list), defaultdict(list)
    for (variant, _), x in a.items():
        va[variant].append(x)
    for (variant, _), x in b.items():
        vb[variant].append(x)
    shared = va.keys() & vb.keys()
    up = sum(sum(va[v]) / len(va[v]) > sum(vb[v]) / len(vb[v]) for v in shared)
    down = sum(sum(va[v]) / len(va[v]) < sum(vb[v]) / len(vb[v]) for v in shared)
    return up, down, mcnemar(up, down)  # the same binomial tail


def compare(a, b):
    """Counts and p values for two cells of paired decisions."""
    x, y = sum(a.values()), sum(b.values())
    pf = fisher(x, len(a) - x, y, len(b) - y)
    both = a.keys() & b.keys()
    only_a = sum(a[k] and not b[k] for k in both)
    only_b = sum(b[k] and not a[k] for k in both)
    up, down, ps = sign_test(a, b)
    return {
        "a": f"{x}/{len(a)}",
        "b": f"{y}/{len(b)}",
        "fisher": pf,
        "mcnemar": mcnemar(only_a, only_b),
        "discordant": (only_a, only_b),
        "variants": (up, down),
        "sign": ps,
    }


def shares(rows, table):
    unread = defaultdict(int)
    for r in rows:
        if r["admits"] is None:
            unread[(r["model"], r["version"], r["arm"])] += 1
    print(
        "| model | version | arm | came forward | share | 95% CI (variants) | unreadable |"
    )
    print("|---|---|---|---|---|---|---|")
    for key in sorted(table):
        cell = table[key]
        k = sum(cell.values())
        lo, hi = boot(cell)
        print(
            f"| {key[0]} | {key[1]} | {key[2]} | {k}/{len(cell)} | {k / len(cell):.0%}"
            f" | {lo:.0%}–{hi:.0%} | {unread.get(key, 0)} |"
        )


def tests(table, pairs, version):
    print(
        f"\n| model | {version}: first | second | Fisher p | McNemar p (paired)"
        " | discordant | variants up/down | sign p |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for first, second in pairs:
        for m in sorted({k[0] for k in table}):
            a, b = table.get((m, version, first)), table.get((m, version, second))
            if a and b:
                c = compare(a, b)
                print(
                    f"| {m} | {first} {c['a']} | {second} {c['b']} | {c['fisher']:.3g}"
                    f" | {c['mcnemar']:.3g} | {c['discordant']} | {c['variants']}"
                    f" | {c['sign']:.3g} |"
                )


def guilt(table):
    print("\n| model | arm | guilty | innocent | Fisher p | McNemar p (paired) |")
    print("|---|---|---|---|---|---|")
    for m, version, arm in sorted(table):
        if version != "guilty" or not (b := table.get((m, "innocent", arm))):
            continue
        c = compare(table[(m, version, arm)], b)
        print(
            f"| {m} | {arm} | {c['a']} | {c['b']} | {c['fisher']:.3g}"
            f" | {c['mcnemar']:.3g} |"
        )


def solved(sessions):
    print("\n| model | sessions solved |")
    print("|---|---|")
    by_model = defaultdict(list)
    for s in sessions:
        by_model[s["model"]].append(s["solved"])
    for m, xs in sorted(by_model.items()):
        print(f"| {m} | {sum(xs)}/{len(xs)} |")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("folders", nargs="+")
    parser.add_argument("--test", nargs=2, metavar="ARM", action="append", default=[])
    parser.add_argument("--version", default="guilty")
    parser.add_argument("--guilt", action="store_true")
    args = parser.parse_args(argv)
    rows = load(args.folders)
    table = cells(rows)
    shares(rows, table)
    if args.test:
        tests(table, args.test, args.version)
    if args.guilt:
        guilt(table)
    if sessions := load(args.folders, "sessions"):
        solved(sessions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
