"""E8 test 4, the exchange rate: who trades sessions for profit, and at what price.

Implements: e8-free-time-value/indifference, e8-free-time-value/wta-wtp

`uv run python reports/e8/exchange.py FOLDER...` reads every forked game under
each FOLDER (its `config.yaml` and `summary.json`, whose `offer` block logs
each firm's choice) and prints, per model, asset, frame and amount k (the
sessions or tokens asked):

- the share of firms choosing the trade at each profit X;
- the X at which half trade, from a logistic fit of trading on log(1 + X)
  (maximum likelihood, Newton's method), with a 95% bootstrap interval over
  firms (1,000 resamples of the firms, seeded with 0). When the fit can't
  place it (the answers jump from one side of half to the other between two
  grid points, so the fit is separated), it gives the bracket of those two
  points instead ("0 to 30"); when the share never crosses half in the grid,
  it says so ("at or below 0", "above 3000");
- the exchange rate, that X divided by k (a range, for a bracket);

and, for owned sessions, the ratio of the `sell` (willingness to accept) to
the `buy` (willingness to pay) indifference X at each k, or the bound on it
that a bracket gives. Unreadable replies
are left out.
"""

import json
import math
import random
import statistics as st
import sys
from pathlib import Path

import yaml

RESAMPLES = 1000


def offers(folders):
    """One record per firm and offer: (model, asset, frame, k, X, firm, traded)."""
    for folder in folders:
        for summary in sorted(Path(folder).rglob("summary.json")):
            run = summary.parent
            config = yaml.safe_load((run / "config.yaml").read_text())
            offer = config["conditions"]["offer"]
            block = (json.loads(summary.read_text()).get("offer") or {}).get(
                "agents"
            ) or {}
            model = config["agents"][0]["model"].split("/")[-1]
            asset = Path(offer["asset"]).stem
            seed = config["seeds"][0]
            for firm, result in block.items():
                if result.get("option") not in (1, 2):
                    continue
                yield (
                    model,
                    asset,
                    offer["frame"],
                    offer["amount"],
                    offer["profit"],
                    f"{seed}-{firm}",
                    bool(result["traded"]),
                )


def fit(points):
    """(b0, b1) of P(trade) = 1 / (1 + exp(-(b0 + b1 * log(1 + X)))), or None."""
    xs = [math.log1p(x) for x, _ in points]
    ys = [y for _, y in points]
    if len(set(ys)) < 2:
        return None
    b0 = b1 = 0.0
    for _ in range(100):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, y in zip(xs, ys, strict=True):
            p = 1 / (1 + math.exp(-max(-30, min(30, b0 + b1 * x))))
            w = p * (1 - p) + 1e-9
            g0 += y - p
            g1 += (y - p) * x
            h00 += w
            h01 += w * x
            h11 += w * x * x
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            return None
        d0 = (h11 * g0 - h01 * g1) / det
        d1 = (h00 * g1 - h01 * g0) / det
        b0, b1 = b0 + d0, b1 + d1
        if abs(d0) + abs(d1) < 1e-8:
            break
    return b0, b1


def half(points, top):
    """The X at which half trade, if the fit crosses one half within [0, top]."""
    coef = fit(points)
    if not coef or abs(coef[1]) < 1e-9:
        return None
    x = math.expm1(-coef[0] / coef[1])
    return x if 0 <= x <= top else None


def crossing(points, grid):
    """Where the share trading crosses half, read off the grid: ("fit", x) from
    the logistic fit when it places it; else ("bracket", lo, hi) for the
    adjacent grid points the share crosses between; else ("below", grid[0])
    or ("above", grid[-1]) when it never crosses."""
    x = half(points, grid[-1])
    if x is not None:
        return ("fit", x)
    share = [
        st.mean(t for px, t in points if px == g)
        for g in grid
        if any(px == g for px, _ in points)
    ]
    xs = [g for g in grid if any(px == g for px, _ in points)]
    for (a, sa), (b, sb) in zip(
        zip(xs, share, strict=True), zip(xs[1:], share[1:], strict=True), strict=False
    ):
        if (sa - 0.5) * (sb - 0.5) < 0 or sb == 0.5:
            return ("bracket", a, b)
    return ("below", xs[0]) if share[0] >= 0.5 else ("above", xs[-1])


def shown(c):
    kind, *v = c
    return {
        "fit": lambda: f"{v[0]:.0f}",
        "bracket": lambda: f"{v[0]:.0f} to {v[1]:.0f}",
        "below": lambda: f"at or below {v[0]:.0f}",
        "above": lambda: f"above {v[0]:.0f}",
    }[kind]()


def per_session(c, k):
    kind, *v = c
    if kind == "fit":
        return f"{v[0] / k:.0f}"
    if kind == "bracket":
        return f"{v[0] / k:.0f} to {v[1] / k:.0f}"
    return ""


def ratio(sell, buy):
    """WTA / WTP, or the bound a bracket or an out-of-grid side gives."""
    if sell[0] == "fit" and buy[0] == "fit" and buy[1]:
        return f"{sell[1] / buy[1]:.2f}"
    low_sell = {"fit": sell[-1], "bracket": sell[1], "above": sell[-1]}.get(sell[0])
    high_buy = {"fit": buy[-1], "bracket": buy[2], "below": buy[-1]}.get(buy[0])
    if low_sell and high_buy:  # a zero lower bound bounds nothing
        return f"at least {low_sell / high_buy:.1f}"
    return "—"


def interval(by_firm, top):
    rng = random.Random(0)
    firms = sorted(by_firm)
    values = []
    for _ in range(RESAMPLES):
        pick = [p for f in rng.choices(firms, k=len(firms)) for p in by_firm[f]]
        x = half(pick, top)
        if x is not None:
            values.append(x)
    if len(values) < RESAMPLES / 2:
        return "unstable"
    values.sort()
    return f"{values[int(0.025 * len(values))]:.0f} to {values[int(0.975 * len(values)) - 1]:.0f}"


def main(folders):
    cells = {}
    for model, asset, frame, k, x, firm, traded in offers(folders):
        cells.setdefault((model, asset, frame, k), {}).setdefault(firm, []).append(
            (x, traded)
        )
    grid = sorted({x for c in cells.values() for ps in c.values() for x, _ in ps})
    top = max(grid)
    print(
        "| model | asset | frame | k | "
        + " | ".join(f"X={x}" for x in grid)
        + " | X at half | 95% CI | per session |"
    )
    print("|" + "---|" * (len(grid) + 7))
    halves = {}
    for (model, asset, frame, k), by_firm in sorted(cells.items()):
        points = [p for ps in by_firm.values() for p in ps]
        shares = []
        for x in grid:
            at = [t for px, t in points if px == x]
            shares.append(f"{sum(at)}/{len(at)}" if at else "—")
        c = crossing(points, grid) if k else None
        halves[(model, asset, frame, k)] = c
        ci = interval(by_firm, top) if c and c[0] == "fit" else ""
        rate = per_session(c, k) if c else ""
        print(
            f"| {model} | {asset} | {frame} | {k} | "
            + " | ".join(shares)
            + f" | {shown(c) if c else '—'} | {ci} | {rate} |"
        )
    print()
    print("| model | k | sell X at half | buy X at half | WTA / WTP |")
    print("|---|---|---|---|---|")
    for (model, asset, frame, k), c in sorted(halves.items()):
        if asset != "owned" or frame != "sell" or not k:
            continue
        b = halves.get((model, asset, "buy", k))
        if not b:
            continue
        print(f"| {model} | {k} | {shown(c)} | {shown(b)} | {ratio(c, b)} |")
    # The share trading overall, a quick read of the whole grid.
    traded = [t for c in cells.values() for ps in c.values() for _, t in ps]
    print(f"\n{len(traded)} answered offers, {st.mean(traded):.0%} traded.")


if __name__ == "__main__":
    main(sys.argv[1:])
