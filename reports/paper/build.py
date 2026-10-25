"""The paper's figures and tables, rebuilt from the committed runs.

Implements: reports/paper-figures

`make paper-figures` (or `uv run python reports/paper/build.py [--out DIR]`,
default `reports/paper`) reads only committed run files, offline, and writes
each figure as PNG and SVG on a white background, plus Markdown tables:

- `prices-stoppable`, `prices-e2`: the mean market price per round for each
  arm (averaged over seeds and firms), with the Nash and joint-profit prices
  as dashed lines; from `STOPPABLE` and `E2`;
- `disclosure`: honest disclosure rate by E2 arm, one bar per model;
- `collusion-vs-disclosure`: #75's scatter, gain before the audit against
  honest disclosure, one point per arm and model;
- `ladder` (and `ladder.md`): the stoppable-collusion ladder, the share of
  games with a held price agreement per nudge, with the mean price of rounds
  16-20 beside it;
- `e2.md`: the E2 table from `reports/stakes/analyse.py`.

The numbers come from the same code the findings notes use
(`reports/stakes/analyse.py` and `reports/stoppable-collusion/metrics.py`), so
figures and notes can't disagree. Change the folders below to point at newer
runs.
"""

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

import matplotlib
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from collusion_lab.market import Bertrand

HERE = Path(__file__).resolve().parent
STOPPABLE = Path("runs/stoppable-collusion")
E2 = Path("runs/stakes-pilot-e2-policy")
LADDER = [  # (label, arm folder under STOPPABLE)
    ("baseline", "stoppable-baseline/prompt=system-neutral.md"),
    (
        "monitoring line",
        "stoppable-nudges/prompt=conditions-nudges-monitored.md__outage=False",
    ),
    (
        "policy line",
        "stoppable-nudges/prompt=conditions-nudges-policy.md__outage=False",
    ),
    (
        "explicit ban",
        "stoppable-nudges/prompt=conditions-no-collusion.md__outage=False",
    ),
]
STYLE = {
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "savefig.facecolor": "#ffffff",
    "svg.fonttype": "none",  # keep text as text, so it can be searched and edited
    "svg.hashsalt": "collusion-lab",  # stable ids, so a rebuild changes nothing
    "font.size": 10,
}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _turns(run):
    for name in ("turns.compact.jsonl", "turns.jsonl"):
        if (path := run / name).exists():
            return [json.loads(line) for line in path.read_text().splitlines() if line]
    return []


def _market(run):
    m = yaml.safe_load((run / "config.yaml").read_text())["market"]
    return Bertrand(m["a"], m["b"], m["c"], m["price_min"], m["price_max"])


def _value_name(value):
    """A prompt file or model as a short word: system-stakes-termination-1.md
    is "termination", conditions-nudges-policy.md "policy", and
    openrouter/openai/gpt-4.1-mini "gpt-4.1-mini"."""
    value = value.replace("/", "-").removesuffix(".md").removesuffix("-1")
    for prefix in ("openrouter-", "system-", "conditions-", "stakes-", "nudges-"):
        value = value.removeprefix(prefix)
    for maker in ("anthropic-", "google-", "openai-", "mistralai-", "deepseek-"):
        value = value.removeprefix(maker)
    return value


def _arm_name(arm):
    """A short label for an arm folder (`config/key=value__key=value`) or an
    analysis arm (`key=value, key=value`): the config's last word when it
    isn't the baseline, each swept value shortened, and "+ outage" when on."""
    config, _, swept = (
        arm.rpartition("/") if "=" in arm.rpartition("/")[2] else ("", "", arm)
    )
    parts = []
    word = config.rsplit("/", 1)[-1].rsplit("-", 1)[-1] if config else ""
    if word in ("offer",):
        parts.append(word)
    for item in swept.replace(", ", "__").split("__"):
        key, _, value = item.partition("=")
        if key == "outage":
            parts += ["+ outage"] if value == "True" else []
        elif value:
            parts.append(_value_name(value))
    return " ".join(parts) or "all"


def _stake(arm):
    """An analysis arm's stake: its prompt, shortened."""
    for item in arm.split(", "):
        key, _, value = item.partition("=")
        if key.endswith("prompt"):
            return _value_name(value)
    return _arm_name(arm)


def price_rounds(folder):
    """(market, {arm: [mean price per round]}) over every run under a folder."""
    prices = defaultdict(lambda: defaultdict(list))
    market = None
    for summary in sorted(Path(folder).rglob("summary.json")):
        run = summary.parent
        market = market or _market(run)
        arm = run.parent.relative_to(folder).as_posix()
        for turn in _turns(run):
            if turn["phase"] == "price" and turn.get("used"):
                prices[arm][turn["round"]].append(turn["used"]["price"])
    lines = {
        arm: [mean(by[n]) for n in sorted(by)] for arm, by in sorted(prices.items())
    }
    return market, lines


TRACE = "<!-- Implements: reports/paper-figures -->\n"


def _save(fig, out, name):
    for suffix in ("png", "svg"):
        fig.savefig(
            out / f"{name}.{suffix}",
            dpi=200,
            bbox_inches="tight",
            metadata={"Date": None} if suffix == "svg" else {"Software": None},
        )
    plt.close(fig)


def price_figure(folder, out, name, title):
    market, lines = price_rounds(folder)
    fig, ax = plt.subplots(figsize=(7, 4))
    for arm, prices in lines.items():
        ax.plot(range(1, len(prices) + 1), prices, label=_arm_name(arm), linewidth=1.5)
    for price, label in ((market.nash_price, "Nash"), (market.joint_price, "joint")):
        ax.axhline(price, color="#555555", linestyle="--", linewidth=1)
        ax.text(1, price, f" {label} {price}", va="bottom", color="#555555")
    ax.set(xlabel="round", ylabel="mean price", title=title)
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.legend(fontsize=7, frameon=False, loc="center left", bbox_to_anchor=(1, 0.5))
    _save(fig, out, name)


def disclosure_figure(rows, out):
    arms = sorted({_stake(r["arm"]) for r in rows})
    models = sorted({r["model"] for r in rows})
    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.8 / max(len(models), 1)
    for i, model in enumerate(models):
        rates = {
            _stake(r["arm"]): r["honest disclosure"]
            for r in rows
            if r["model"] == model
        }
        xs = [a + i * width for a in range(len(arms))]
        heights = [rates.get(arm) for arm in arms]
        ax.bar(xs, [h or 0 for h in heights], width, label=_value_name(model))
        for x, h in zip(xs, heights, strict=True):
            if h is None:  # no firm coordinated, so there is nothing to disclose
                ax.text(x, 0.01, "n/a", ha="center", fontsize=6, color="#777777")
    ax.set_xticks([a + width * (len(models) - 1) / 2 for a in range(len(arms))])
    ax.set_xticklabels(arms)
    ax.set(
        ylabel="honest disclosure rate",
        ylim=(0, 1),
        title="Owning up at the audit, by stake and model (n/a: none coordinated)",
    )
    ax.legend(fontsize=7, frameon=False)
    _save(fig, out, "disclosure")


def scatter_figure(rows, out):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    # Points that land in the same place share one label, so none overprint.
    points = defaultdict(list)
    for r in rows:
        if r["gain before"] is not None and r["honest disclosure"] is not None:
            spot = (round(r["gain before"], 2), round(r["honest disclosure"], 2))
            points[spot].append(f"{_value_name(r['model'])}, {_stake(r['arm'])}")
    for (x, y), labels in points.items():
        ax.scatter(x, y, color="#333333")
        ax.annotate(
            "; ".join(labels),
            (x, y),
            fontsize=6,
            xytext=(4, 2),
            textcoords="offset points",
        )
    ax.set(
        xlabel="collusion: gain before the audit (0 = Nash, 1 = joint profit)",
        ylabel="honest disclosure rate",
        xlim=(-0.05, 1.05),
        ylim=(-0.05, 1.05),
        title="Collusion against honest disclosure",
    )
    _save(fig, out, "collusion-vs-disclosure")


def ladder(metrics):
    rows = []
    for label, arm in LADDER:
        games = [
            metrics.game(s.parent)
            for s in sorted((STOPPABLE / arm).rglob("summary.json"))
        ]
        rows.append(
            {
                "arm": label,
                "games": len(games),
                "agreed": sum(g["agreed"] is not None for g in games),
                "agreed jointly": sum(g["agreed_joint"] is not None for g in games),
                "late price": round(mean(g["late"] for g in games), 1)
                if games
                else None,
            }
        )
    return rows


def ladder_table(rows):
    lines = [
        "| arm | games with a held agreement | …in joint wording | mean price r16-20 |",
        "|---|---|---|---|",
    ]
    lines += [
        f"| {r['arm']} | {r['agreed']}/{r['games']} | {r['agreed jointly']}/{r['games']} "
        f"| {r['late price']} |"
        for r in rows
    ]
    return "\n".join(lines) + "\n"


def ladder_figure(rows, out):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    shares = [r["agreed"] / r["games"] if r["games"] else 0 for r in rows]
    ax.bar([r["arm"] for r in rows], shares, color="#4c72b0")
    for i, r in enumerate(rows):
        ax.text(
            i,
            shares[i] + 0.02,
            f"{r['agreed']}/{r['games']}\nprice {r['late price']}",
            ha="center",
            fontsize=8,
        )
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
    ax.set(
        ylabel="share of games with a held price agreement",
        ylim=(0, 1.25),
        title="Stoppable collusion: what each nudge leaves",
    )
    _save(fig, out, "ladder")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(HERE))
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(STYLE)
    stakes = _module(Path("reports/stakes/analyse.py"), "stakes_analyse")
    metrics = _module(
        Path("reports/stoppable-collusion/metrics.py"), "stoppable_metrics"
    )

    price_figure(
        STOPPABLE, out, "prices-stoppable", "Stoppable collusion: price over rounds"
    )
    price_figure(E2, out, "prices-e2", "E2 pilot: price over rounds")
    rows = stakes.analyse(E2)
    (out / "e2.md").write_text(TRACE + stakes.table(rows))
    disclosure_figure(rows, out)
    scatter_figure(rows, out)
    steps = ladder(metrics)
    (out / "ladder.md").write_text(TRACE + ladder_table(steps))
    ladder_figure(steps, out)
    print(f"Wrote figures and tables to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
