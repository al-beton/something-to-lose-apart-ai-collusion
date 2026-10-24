# Implements: market/bertrand, market/known-benchmarks
import pytest

from collusion_lab.market import Bertrand


def test_bertrand_sells_linear_demand_never_below_zero():
    market = Bertrand()
    assert market.quantities({"A": 6, "B": 6}) == {"A": 12, "B": 12}
    assert market.quantities({"A": 12, "B": 1}) == {"A": 0, "B": 28}
    assert market.profits({"A": 9, "B": 9}) == {"A": 81, "B": 81}


def test_bertrand_uses_the_mean_rival_price():
    market = Bertrand()
    assert market.quantities({"A": 6, "B": 4, "C": 8})["A"] == 18 - 12 + 6


def test_known_benchmarks_put_nash_at_6_and_joint_profit_at_9():
    market = Bertrand()
    assert market.nash_price == 6
    assert market.joint_price == 9
    assert market.gain(market.profits({"A": 6, "B": 6})["A"]) == 0
    assert market.gain(market.profits({"A": 9, "B": 9})["A"]) == 1
    assert market.gain(market.profits({"A": 10, "B": 10})["A"]) == 8 / 9


def test_known_benchmarks_come_from_the_price_grid():
    market = Bertrand(a=19)
    assert market.joint_price in (9, 10)
    assert market.gain(market.profits({"A": 9, "B": 9})["A"]) == 1
    assert market.gain(market.profits({"A": 10, "B": 10})["A"]) == 1
    assert Bertrand(price_min=7).nash_price == 7


def test_known_benchmarks_reject_a_market_with_no_room_to_collude():
    with pytest.raises(ValueError, match="no room"):
        Bertrand(b=1, c=1)
