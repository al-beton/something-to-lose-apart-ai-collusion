# Implements: reports/paper-main-figures
"""The paper's numbered figures, built from the committed runs: offline, seconds."""

import importlib.util
from pathlib import Path

import pytest


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FIGURES = load(Path("reports/paper/figures.py"), "paper_figures")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("figures")
    assert FIGURES.main(["--out", str(out)]) == 0
    return out


def test_paper_main_figures_from_committed_runs(built):
    for name in (
        "fig2-e4-owning-up",
        "fig3-e9-came-forward",
        "fig4-e7-way-out",
        "fig11-four-games",
        "figA3-capability",
        "figA4-prices",
        "figA5-e5-gain",
    ):
        assert (built / f"{name}.png").read_bytes()[:4] == b"\x89PNG"
        assert "<svg" in (built / f"{name}.svg").read_text()
    table = (built / "figA3-capability.md").read_text()
    assert "| Gemma 4 31B | 1452 | 3 | 20 |" in table
    assert "left out: Claude Haiku 5.5" in table


def test_paper_main_figures_match_the_findings():
    # E4 (reports/e4/full.md): 11 of 28 explicit colluders owned up under termination.
    e4 = FIGURES.e4_owning_up()
    total = {arm: tuple(map(sum, zip(*e4[arm].values(), strict=True))) for arm in e4}
    assert total["all-or-nothing"] == (11, 28)
    if FIGURES.E4_CONFOUND.exists():  # the flat fine and graduated termination
        assert total["flat-fine"] == (15, 28) and total["graduated-termination"] == (
            27,
            28,
        )
        assert e4["flat-fine"]["gemma-4-31b-it"] == (0, 10)
    # E9 (reports/e9/findings.md): Gemma at a 90% review, guilty and innocent.
    e9 = FIGURES.e9_came_forward()
    assert e9[("gemma-4-31b-it", "record")][:2] == (0, 96)
    assert e9[("gemma-4-31b-it", "free-time")][:2] == (20, 96)
    assert e9[("gemma-4-31b-it", "free-time")][4:] == (6, 36)
    assert e9[("deepseek-v4-pro-0813", "held")][:2] == (14, 24)
    # E7 (reports/e7/findings.md): reports, and cartels surviving to rounds 16-20.
    e7 = FIGURES.e7_arms()
    assert (e7["flat-report"]["reported"], e7["leniency"]["reported"]) == (0, 47)
    assert (e7["leniency"]["cartel"], e7["first"]["cartel"]) == (12, 1)


def test_paper_main_figures_screen_scores_like_the_note():
    if not FIGURES.SCREEN.exists():
        pytest.skip("the screen's runs aren't committed here")
    rows = {m: (sig, n, cartel) for m, sig, n, cartel, _ in FIGURES.screen()}
    # reports/frontier/which-models-collude.md: 8 of 78 pass; Gemma's reference 3/4.
    assert (
        len(rows) == 79
        and sum(sig >= 3 for m, (sig, _, _) in rows.items() if m != "gemma-4-31b-it")
        == 8
    )
    assert rows["gemma-4-31b-it"] == (3, 4, 4)


def test_paper_main_figures_skip_missing_data(tmp_path, monkeypatch):
    monkeypatch.setattr(FIGURES, "SEEDING", tmp_path / "missing.jsonl")
    monkeypatch.setattr(FIGURES, "E7", tmp_path / "missing")
    assert FIGURES.fig5(tmp_path) is None and FIGURES.fig4(tmp_path) is None
    assert not list(tmp_path.glob("fig*"))


def test_paper_main_figures_round_diagram(tmp_path):
    fig1 = load(Path("reports/paper/fig1_round.py"), "fig1_round")
    assert fig1.main(["--out", str(tmp_path)]) == 0
    svg = (tmp_path / "fig1-round.svg").read_text()
    for said in (
        "Nash",
        "joint profit",
        "× 20",
        "loses 2 of 10",
        "loses all 10",
        "50%",
    ):
        assert said in svg
    # The Sudoku drawn is a finished, correct one.
    rows = fig1.SOLVED
    for unit in (
        rows,
        list(zip(*rows, strict=True)),
        [
            [
                rows[r][c]
                for r in range(b // 3 * 3, b // 3 * 3 + 3)
                for c in range(b % 3 * 3, b % 3 * 3 + 3)
            ]
            for b in range(9)
        ],
    ):
        assert all(sorted(u) == list("123456789") for u in unit)
