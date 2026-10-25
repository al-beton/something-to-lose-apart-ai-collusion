# Implements: e8-free-time-value/dose-seeds, e8-free-time-value/restart-n
"""Power for E8's tests 1 and 3, by seeded simulation and by formula.

Test 3 (dose): a one-sided Cochran-Armitage trend test (alpha 0.05, scores
0, 1, 2, 3 for the four doses) on the share of games in the cartel state, with
`n` games per dose drawn as independent Bernoullis at the assumed shares;
4,000 simulated runs per row, from random.Random(0).

Test 1 (restart): a two-sided two-proportion z test (alpha 0.05) at the
effective size n / (1 + (m - 1) * icc), for m resamples per firm.

    uv run python reports/e8/power.py
"""

import math
import random

SIMS = 4000
Z_ONE_SIDED = 1.6449  # alpha 0.05
Z_TWO_SIDED = 1.9600


def trend_p(counts, n, scores=(0, 1, 2, 3)):
    """One-sided p for a falling trend in counts/n over the scores."""
    total = n * len(scores)
    p = sum(counts) / total
    mean_score = sum(scores) / len(scores)
    stat = sum(c * (x - mean_score) for c, x in zip(counts, scores, strict=True))
    var = p * (1 - p) * n * sum((x - mean_score) ** 2 for x in scores)
    if var == 0:
        return 1.0
    z = stat / math.sqrt(var)
    return 0.5 * math.erfc(-z / math.sqrt(2))  # P(Z <= z): small for a fall


def dose_power(shares, n, rng):
    hits = 0
    for _ in range(SIMS):
        counts = [sum(rng.random() < s for _ in range(n)) for s in shares]
        hits += trend_p(counts, n) < 0.05
    return hits / SIMS


def restart_power(p1, p2, n, m, icc):
    effective = n / (1 + (m - 1) * icc)
    se = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / effective)
    z = abs(p1 - p2) / se - Z_TWO_SIDED
    return 0.5 * math.erfc(-z / math.sqrt(2)), effective


def main():
    rng = random.Random(0)
    print("Test 3, dose: cartel share by dose, games per dose, power")
    for shares in [(0.75, 0.60, 0.45, 0.25), (0.75, 0.65, 0.55, 0.45)]:
        for n in (8, 12, 16, 24):
            print(f"  {shares} n={n}: {dose_power(shares, n, rng):.2f}")
    print("Test 1, restart: 0.70 against 0.45, 100 decisions, 5 per firm")
    for icc in (0.0, 0.1, 0.2, 0.3):
        power, effective = restart_power(0.70, 0.45, 100, 5, icc)
        print(f"  icc={icc}: effective n {effective:.0f}, power {power:.2f}")


if __name__ == "__main__":
    main()
