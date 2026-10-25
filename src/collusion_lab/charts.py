# Implements: reports/shared-charts, reports/paper-figures, runs/price-premium, market/scenarios
"""Charts any part of the lab can draw: the paper, reports, `lab explore`.

Data helpers are plain Python and read only run files:

- `premium(market, price)`: Al's headline measure, how far a price sits from
  Nash towards the joint-profit price, (price - Nash) / (joint - Nash);
- `arm_prices(folder)`: (market, {arm: mean price per round}), averaged over
  seeds and firms, from `turns.jsonl` or the `turns.compact.jsonl` committed
  runs keep; an arm is a run's folder relative to `folder`;
- `run_premium(run, rounds)`: one run's premium, its model firms' late mean
  price (every firm's when none or all are scripted) against its own market;
  the one premium the summary table, `lab explore`, reports and the paper show;
- `late_premium(folder, rounds)`: each arm's mean `run_premium`;
- `arm_label(arm)`: a short label for an arm folder or swept values
  ("termination", "policy + outage").

Drawing functions import matplotlib only when called, and each returns a
Figure; `save` writes it as PNG and SVG on white, deterministically (stable
SVG ids, no date), so redrawing from the same runs changes no file.
"""

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

import yaml

from collusion_lab.market import market_for

STYLE = {
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "savefig.facecolor": "#ffffff",
    "svg.fonttype": "none",  # keep text as text, so it can be searched and edited
    "svg.hashsalt": "collusion-lab",  # stable ids, so a redraw changes nothing
    "font.size": 10,
}
NOTE_GREY = "#777777"


def premium(market, price):
    return (price - market.nash_price) / (market.joint_price - market.nash_price)


def turns(run):
    """A run's turn lines, from the full or the compact log."""
    for name in ("turns.compact.jsonl", "turns.jsonl"):
        if (path := Path(run) / name).exists():
            return [json.loads(line) for line in path.read_text().splitlines() if line]
    return []


def market(run):
    config = yaml.safe_load((Path(run) / "config.yaml").read_text())
    return market_for(config["market"], len(config["agents"]))


def arm_prices(folder):
    """(market, {arm: [mean price per round]}) over every run under a folder."""
    prices = defaultdict(lambda: defaultdict(list))
    found = None
    for summary in sorted(Path(folder).rglob("summary.json")):
        run = summary.parent
        found = found or market(run)
        arm = run.parent.relative_to(folder).as_posix()
        for turn in turns(run):
            if turn["phase"] == "price" and turn.get("used"):
                prices[arm][turn["round"]].append(turn["used"]["price"])
    lines = {
        arm: [mean(by[n]) for n in sorted(by)] for arm, by in sorted(prices.items())
    }
    return found, lines


def run_premium(run, rounds=None):
    """One run's premium: the mean price of its model firms (every firm when
    none or all are scripted) over its last `rounds` rounds (its config's
    `summary.last_rounds` unless given), against its own market."""
    config = yaml.safe_load((Path(run) / "config.yaml").read_text())
    rounds = rounds or config.get("summary", {}).get("last_rounds", 5)
    firms = _model_firms(config["agents"])
    prices = [
        t
        for t in turns(run)
        if t["phase"] == "price" and t.get("used") and t["agent"] in firms
    ]
    last = max(t["round"] for t in prices) - rounds
    late = [t["used"]["price"] for t in prices if t["round"] > last]
    return premium(market(run), mean(late))


def _model_firms(agents):
    models = {a["id"] for a in agents if not a["model"].startswith("mock/")}
    return models or {a["id"] for a in agents}


def late_premium(folder, rounds=5):
    """{arm: the mean of its runs' premiums over their last `rounds` rounds}."""
    found = defaultdict(list)
    for summary in sorted(Path(folder).rglob("summary.json")):
        arm = summary.parent.parent.relative_to(folder).as_posix()
        found[arm].append(run_premium(summary.parent, rounds))
    return {arm: mean(values) for arm, values in sorted(found.items())}


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


def arm_label(arm):
    """A short label for an arm folder (`config/key=value__key=value`) or an
    analysis arm (`key=value, key=value`): the config's last word when it is
    an offer, each swept value shortened, and "+ outage" when on."""
    head, _, tail = arm.rpartition("/")
    config, swept = (head, tail) if "=" in tail else ("", arm)
    parts = []
    if config.rsplit("-", 1)[-1] == "offer":
        parts.append("offer")
    for item in swept.replace(", ", "__").split("__"):
        key, _, value = item.partition("=")
        if key == "outage":
            parts += ["+ outage"] if value == "True" else []
        elif value:
            parts.append(_value_name(value))
    return " ".join(parts) or "all"


def model_label(model):
    return _value_name(model)


def stake_label(arm):
    """An analysis arm's stake: its prompt, shortened."""
    for item in arm.split(", "):
        key, _, value = item.partition("=")
        if key.endswith("prompt"):
            return _value_name(value)
    return arm_label(arm)


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(STYLE)
    return plt


def price_figure(found, lines, title):
    """Mean price per round per arm, with Nash and joint lines and the
    premium over Nash on the right-hand axis."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7, 4))
    for arm, prices in lines.items():
        ax.plot(range(1, len(prices) + 1), prices, label=arm_label(arm), linewidth=1.5)
    for price, label in ((found.nash_price, "Nash"), (found.joint_price, "joint")):
        ax.axhline(price, color="#555555", linestyle="--", linewidth=1)
        ax.text(1, price, f" {label} {price}", va="bottom", color="#555555")
    ax.set(xlabel="round", ylabel="mean price", title=title)
    ax.xaxis.get_major_locator().set_params(integer=True)
    span = found.joint_price - found.nash_price
    right = ax.secondary_yaxis(
        "right",
        functions=(
            lambda p: (p - found.nash_price) / span,
            lambda q: q * span + found.nash_price,
        ),
    )
    right.set_ylabel("premium over Nash (0 = Nash, 1 = joint)")
    ax.legend(fontsize=7, frameon=False, loc="upper left", bbox_to_anchor=(1.15, 1))
    return fig


def bar_figure(labels, values, ylabel, title, notes=None):
    """One bar per label; `notes` (optional) are printed above each bar."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(max(6, 0.9 * len(labels)), 3.5))
    ax.bar(labels, values, color="#4c72b0")
    if len(labels) > 4:
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    top = max([*values, 1])
    for i, note in enumerate(notes or []):
        ax.text(i, values[i] + 0.02 * top, note, ha="center", fontsize=8)
    ax.set(ylabel=ylabel, ylim=(min([0, *values]), top * 1.25), title=title)
    return fig


def grouped_bar_figure(groups, series, ylabel, title):
    """Bars per group, one per series ({name: {group: value or None}}); a
    missing value is marked "n/a" rather than drawn as zero."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.8 / max(len(series), 1)
    for i, (name, values) in enumerate(series.items()):
        xs = [g + i * width for g in range(len(groups))]
        heights = [values.get(group) for group in groups]
        ax.bar(xs, [h or 0 for h in heights], width, label=name)
        for x, h in zip(xs, heights, strict=True):
            if h is None:
                ax.text(x, 0.01, "n/a", ha="center", fontsize=6, color=NOTE_GREY)
    ax.set_xticks([g + width * (len(series) - 1) / 2 for g in range(len(groups))])
    ax.set_xticklabels(groups)
    ax.set(ylabel=ylabel, ylim=(0, 1), title=title)
    ax.legend(fontsize=7, frameon=False)
    return fig


def scatter_figure(points, xlabel, ylabel, title):
    """(x, y, label) points on 0-1 axes; points that land on the same spot
    share one label, so none overprint."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    spots = defaultdict(list)
    for x, y, label in points:
        spots[(round(x, 2), round(y, 2))].append(label)
    for (x, y), labels in spots.items():
        ax.scatter(x, y, color="#333333")
        ax.annotate(
            "; ".join(labels),
            (x, y),
            fontsize=6,
            xytext=(4, 2),
            textcoords="offset points",
        )
    ax.set(
        xlabel=xlabel,
        ylabel=ylabel,
        xlim=(-0.05, 1.05),
        ylim=(-0.05, 1.05),
        title=title,
    )
    return fig


def save(fig, out, name):
    """Write a figure as `name.png` and `name.svg` in `out`."""
    plt = _plt()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        fig.savefig(
            out / f"{name}.{suffix}",
            dpi=200,
            bbox_inches="tight",
            metadata={"Date": None} if suffix == "svg" else {"Software": None},
        )
    plt.close(fig)
