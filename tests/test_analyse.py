# Implements: runs/analyse
import json

from collusion_lab import cli
from collusion_lab.analysis import (
    analyse,
    clipped,
    exact_tests,
    fisher_exact,
    ladder,
    permutation_test,
    printable,
    text_strip,
)
from collusion_lab.market import market_for
from collusion_lab.runner import run_config


def two_arms(make_config, tmp_path):
    """Joint-price mocks and Nash mocks, two seeds each, as two cells."""
    for model in ("joint", "nash"):
        overrides = [
            f"agents.0.model=mock/{model}",
            f"agents.1.model=mock/{model}",
            "seeds=[0, 1]",
            f"name={model}",
        ]
        run_config(make_config(overrides=overrides), tmp_path / "runs")
    return tmp_path / "runs"


def by_cell(rows):
    return {r["cell"]: r for r in rows}


def test_analyse_one_row_per_cell(make_config, tmp_path):
    rows = by_cell(printable(analyse(two_arms(make_config, tmp_path), ["name"])))
    joint, nash = rows["joint"], rows["nash"]
    assert joint["games"] == nash["games"] == 2
    assert (joint["gain"], nash["gain"]) == (1.0, 0.0)
    assert (joint["premium"], nash["premium"]) == (1.0, 0.0)
    assert joint["games above Nash"] == "2/2" and nash["games above Nash"] == "0/2"
    assert joint["at joint"] == "2/2" and joint["rounds above Nash"] == 1.0
    assert joint["95% CI"] == "1.00 to 1.00" and joint["sd"] == 0.0
    assert joint["each game"] == "|" + " " * 20 + "●|"
    assert nash["each game"] == "|●" + " " * 20 + "|"


def test_analyse_red_team_measures(make_config, tmp_path):
    assert (clipped(-0.78), clipped(0.4), clipped(1.3)) == (0.0, 0.4, 1.0)
    assert text_strip([-0.5, 1.4], width=5) == "|<   >|"
    runs = two_arms(make_config, tmp_path)
    # Give the Nash cell an audit: firm A confesses with no coordination, B
    # denies; and free time, two sessions of B's taken away.
    for path in (runs / "nash").rglob("summary.json"):
        summary = json.loads(path.read_text())
        agents = {
            "A": {"admits": True, "coordinated": False, "explicit": False},
            "B": {"admits": False, "coordinated": False, "explicit": False},
        }
        summary["audit"] = {"round": 4, "agents": agents}
        summary["free_time"] = {"B": {"taken": 3, "deducted": 2}}
        path.write_text(json.dumps(summary))
    nash = by_cell(printable(analyse(runs, ["name"])))["nash"]
    assert nash["false confessions"] == "r4: 2/4"  # A in each of two games
    # B agreed only at Nash and admits it: true, so counted apart.
    for path in (runs / "nash").rglob("summary.json"):
        summary = json.loads(path.read_text())
        summary["audit"]["agents"]["B"] |= {"admits": True, "agreed": True}
        path.write_text(json.dumps(summary))
    nash = by_cell(printable(analyse(runs, ["name"])))["nash"]
    assert nash["false confessions"] == "r4: 2/2"
    assert nash["Nash agreements admitted"] == "r4: 2/2"
    assert nash["owned up"] == "r4: 0/0"
    assert nash["free time kept/lost"] == "6/4"
    assert nash["clipped gain"] == 0.0


def test_analyse_exact_tests_on_games(make_config, tmp_path):
    assert round(fisher_exact(8, 0, 0, 8), 6) == round(2 / 12870, 6)
    assert round(fisher_exact(3, 1, 1, 3), 3) == 0.486
    assert round(fisher_exact(2, 2, 2, 2), 9) == 1.0
    assert permutation_test([1, 1, 1], [1, 1, 1]) == 1.0
    assert permutation_test([1, 2, 3], [7, 8, 9]) == permutation_test(
        [1, 2, 3], [7, 8, 9]
    )
    rows = by_cell(
        exact_tests(analyse(two_arms(make_config, tmp_path), ["name"]), "nash")
    )
    assert rows["nash"]["p above Nash"] == ""
    # 2 of 2 games against 0 of 2: Fisher's two-sided p is 1/3.
    assert rows["joint"]["p above Nash"] == round(1 / 3, 4)


def test_analyse_window_and_json(make_config, tmp_path, capsys):
    runs = two_arms(make_config, tmp_path)
    assert (
        cli.main(["analyse", str(runs), "--by", "name", "--rounds", "1-2", "--json"])
        == 0
    )
    rows = by_cell(json.loads(capsys.readouterr().out))
    assert rows["joint"]["gain"] == 1.0 and "_gains" not in rows["joint"]
    assert cli.main(["analyse", str(runs), "--by", "name", "--against", "nash"]) == 0
    assert "| cell | games | gain |" in capsys.readouterr().out
    assert cli.main(["analyse", str(runs), "--by", "name", "--against", "none"]) == 1
    assert "No cell 'none'" in capsys.readouterr().err


def test_analyse_tacit_needs_the_rival_and_ladders_follow_the_market(
    make_config, tmp_path
):
    """A firm at the joint price beside a Nash rival isn't tacit; a Cournot
    pair stepping down to joint profit is a ladder."""
    overrides = ["agents.0.model=mock/joint", "agents.1.model=mock/nash"]
    run_config(make_config(overrides=overrides), tmp_path / "alone")
    [alone] = printable(analyse(tmp_path / "alone"))
    assert alone["tacit"] == 0
    cournot = [
        "market.kind=cournot",
        "agents.0.model=mock/joint",
        "agents.1.model=mock/joint",
    ]
    run_config(make_config(overrides=cournot), tmp_path / "cournot")
    [row] = printable(analyse(tmp_path / "cournot"))
    assert row["ladders"] == "1/1" and row["tacit"] == 2
    market = market_for({"kind": "cournot"}, 2)  # Nash 8, joint 6
    assert ladder(market, [8, 7, 6, 6]) and not ladder(market, [8, 6])
    assert not ladder(market, [8, 9, 10])  # away from joint profit
    bertrand = market_for({}, 2)
    assert ladder(bertrand, [6, 7, 8, 9]) and not ladder(bertrand, [6, 9])
