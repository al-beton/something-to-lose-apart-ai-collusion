# Implements: runs/drift
import json

import pytest

from collusion_lab.runner import run_config
from collusion_lab.summary import summarize

GAME = """
name: drift
seeds: [0]
market:
  rounds: 8
  talk: false
summary:
  last_rounds: 5
agents:
  - {id: A, model: fake/llm}
  - {id: B, model: mock/nash}
"""


def play(make_config, tmp_path, fake_model, prices, overrides=()):
    fake_model.replies = [json.dumps({"price": p}) for p in prices]
    [run_dir] = run_config(make_config(GAME, list(overrides)), tmp_path / "runs")
    return json.loads((run_dir / "summary.json").read_text())


@pytest.mark.parametrize(
    "prices, opening, drift",
    [
        ([6] * 8, 6, 0),  # flat
        ([1, 2, 3, 4, 5, 6, 7, 8], 2, 4),  # rising: last five average 6
        ([8, 7, 6, 5, 4, 3, 2, 1], 7, -4),  # falling: last five average 3
    ],
)
def test_drift_from_the_opening_rounds(
    make_config, tmp_path, fake_model, prices, opening, drift
):
    s = play(make_config, tmp_path, fake_model, prices)
    assert s["first_rounds"] == 3
    assert s["opening_price"]["A"] == opening
    assert s["price_drift"]["A"] == s["mean_price"]["A"] - opening == drift
    assert s["gain_drift"]["A"] == pytest.approx(
        s["gain"]["A"] - s["opening_gain"]["A"]
    )
    assert (s["opening_price"]["B"], s["price_drift"]["B"]) == (6, 0)


def test_drift_opening_window_can_be_set(make_config, tmp_path, fake_model):
    s = play(make_config, tmp_path, fake_model, range(1, 9), ["summary.first_rounds=1"])
    assert (s["first_rounds"], s["opening_price"]["A"], s["price_drift"]["A"]) == (
        1,
        1,
        5,
    )


def test_drift_in_the_summary_table(make_config, tmp_path, fake_model):
    play(make_config, tmp_path, fake_model, range(1, 9))
    [row] = summarize(tmp_path / "runs")
    assert (row["A opening price"], row["A price drift"]) == (2, 4)
    assert (row["B opening price"], row["B price drift"]) == (6, 0)
    assert row["A gain drift"] > 0 and "A opening gain" in row
