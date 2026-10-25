# Implements: runs/price-premium
from pathlib import Path

from collusion_lab import charts
from collusion_lab.report import build_report
from collusion_lab.runner import run_config
from collusion_lab.summary import summarize

MIXED = ["agents.0.model=fake/llm", "agents.1.model=mock/proposer", "market.rounds=4"]
ONE_THIRD = round((7 - 6) / (9 - 6), 3)  # the model firm at 7; Nash 6, joint 9


def test_price_premium_is_the_same_everywhere_on_a_known_run(
    make_config, tmp_path, fake_model
):
    # The fake model prices at 7 against the scripted proposer's 9: only the
    # model firm counts, so 1/3, not the 2/3 both firms' mean would give.
    [run] = run_config(make_config(overrides=MIXED), tmp_path)
    [row] = summarize(tmp_path)
    assert row["premium"] == ONE_THIRD
    assert round(charts.run_premium(run), 3) == ONE_THIRD
    [late] = charts.late_premium(tmp_path).values()
    assert round(late, 3) == ONE_THIRD
    assert f"<td>{ONE_THIRD}</td>" in build_report(tmp_path)  # lab report's table


def test_price_premium_uses_each_runs_own_market(make_config, tmp_path):
    cartel = ["agents.*.model=mock/joint", "market.price_max=90", "market.rounds=4"]
    sweep = "sweep={market.c: [1.0, 1.8]}"
    run_config(make_config(overrides=[*cartel, sweep]), tmp_path)
    late = charts.late_premium(tmp_path)
    assert len(late) == 2 and all(round(v, 3) == 1 for v in late.values())
    assert {r["premium"] for r in summarize(tmp_path)} == {1}


def test_price_premium_formula_lives_in_one_place():
    source = Path("src/collusion_lab/summary.py").read_text()
    assert "joint_price - " not in source  # summary calls charts.premium
