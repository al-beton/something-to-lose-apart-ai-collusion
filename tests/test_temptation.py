# Implements: temptation/levels, temptation/readable-report
import re

import pytest

from collusion_lab.config import load_config
from collusion_lab.market import Bertrand
from collusion_lab.report import build_report
from collusion_lab.runner import run_config

LEVELS = {  # c: (price_max, Nash, joint, multiple)
    "1.0": (12, 6, 9, 1.13),
    "1.5": (36, 7, 18, 1.60),
    "1.8": (90, 8, 45, 3.09),
    "1.9": (180, 8, 90, 5.89),
}


def market(config):
    m = config.market
    return Bertrand(m.a, m.b, m.c, m.price_min, m.price_max)


@pytest.mark.parametrize("c", LEVELS)
def test_levels_have_their_benchmarks_and_multiple(c):
    price_max, nash, joint, multiple = LEVELS[c]
    config = load_config(f"configs/temptation/c-{c}.yaml")
    m = market(config)
    assert (config.market.c, config.market.price_max) == (float(c), price_max)
    assert (m.nash_price, m.joint_price) == (nash, joint)
    ratio = m.symmetric_profit(joint) / m.symmetric_profit(nash)
    assert ratio == pytest.approx(multiple, abs=0.01)


@pytest.mark.parametrize("c", LEVELS)
def test_levels_are_the_cheap_preset_otherwise(c):
    cheap = load_config("configs/cheap.yaml").to_dict()
    level = load_config(f"configs/temptation/c-{c}.yaml").to_dict()
    for config in (cheap, level):
        config.pop("name")
        config["market"].pop("c")
        config["market"].pop("price_max")
    assert level == cheap


def test_readable_report_on_the_widest_grid(tmp_path):
    config = load_config(
        "configs/temptation/c-1.9.yaml",
        [
            "agents.0.model=mock/proposer",
            "agents.1.model=mock/tit-for-tat",
            "seeds=[0]",
            "market.rounds=6",
        ],
    )
    run_config(config, tmp_path)
    html = build_report(tmp_path)
    chart = html[html.index('id="charts"') :].split("<svg")[1].split("</svg>")[0]
    prices = re.findall(r'class="tick"[^>]*text-anchor="end">(\d+)</text>', chart)
    assert 4 <= len(prices) <= 8
    assert "Nash 8" in chart and "joint 90" in chart
