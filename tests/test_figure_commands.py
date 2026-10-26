# Implements: reproducibility/figure-commands
"""Each registered figure: redrawn free from committed runs, or played again
at cost into a folder of its own."""

import importlib.util
import json
import re
import shutil
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from collusion_lab.config import load_config
from collusion_lab.runner import run_config


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FIGURE = load(Path("reports/paper/figure.py"), "paper_figure")


@pytest.mark.parametrize("figure", FIGURE.FIGURES)
def test_figure_commands_replay_matches_the_committed_figure(figure):
    assert FIGURE.replay(FIGURE.FIGURES[figure]) == []


def test_figure_commands_replay_fails_on_a_changed_figure(tmp_path):
    figure = FIGURE.FIGURES["e4-owning-up"]
    for path in FIGURE.COMMITTED.glob(f"{figure.name}.*"):
        shutil.copy(path, tmp_path)
    svg = tmp_path / f"{figure.name}.svg"
    svg.write_text(svg.read_text().replace("owned up", "owned  up", 1))
    assert FIGURE.replay(figure, committed=tmp_path) == [
        f"{figure.name}.svg: differs from {svg}"
    ]
    assert FIGURE.main(["replay", "e4-owning-up"]) == 0


@pytest.mark.parametrize("figure", FIGURE.FIGURES)
def test_figure_commands_registry_runs_alone_draw_the_figure(figure, tmp_path):
    """The runs the registry names are enough: the figure drawn from a copy
    holding only them is the committed one, so regenerating them is too."""
    figure = FIGURE.FIGURES[figure]
    figs = FIGURE.figures_module()
    for run in figure.runs(figs):
        shutil.copytree(run, tmp_path / run)
    for attr in figure.folders:
        setattr(figs, attr, tmp_path / getattr(figs, attr))
    drawn = FIGURE.draw(figure, tmp_path / "figures", figs)
    assert drawn
    for path in drawn:
        assert FIGURE.shown(path) == FIGURE.shown(FIGURE.COMMITTED / path.name)


def test_figure_commands_replay_ignores_how_fonts_draw(tmp_path):
    """Another machine's fonts move every glyph and pixel but no label: the
    figure still replays."""
    figure = FIGURE.FIGURES["e4-owning-up"]
    for path in FIGURE.COMMITTED.glob(f"{figure.name}.*"):
        shutil.copy(path, tmp_path)
    svg = tmp_path / f"{figure.name}.svg"
    svg.write_text(re.sub(r' d="[^"]*"', ' d="M 0 0"', svg.read_text()))
    (tmp_path / f"{figure.name}.png").write_bytes(b"other pixels")
    assert FIGURE.replay(figure, committed=tmp_path) == []


MOCK = f"""
name: mock-figure
prompts_dir: {Path("prompts").resolve()}
seeds: [0]
market:
  rounds: 3
summary:
  last_rounds: 2
agents:
  - {{id: A, model: mock/nash}}
  - {{id: B, model: mock/nash}}
"""


@pytest.fixture
def small_figure(tmp_path, monkeypatch):
    """A registered figure over one committed run of the cwd, drawn by a
    stand-in builder that records the folder it was pointed at."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text(textwrap.dedent(MOCK))
    [run] = run_config(load_config(tmp_path / "config.yaml"), Path("runs/mock"))
    seen = {}

    def build(out):
        seen["folder"] = figs.FOLDER
        out.mkdir(parents=True, exist_ok=True)
        (out / "mock.svg").write_text(str(sorted(figs.FOLDER.rglob("summary.json"))))
        return "mock"

    figs = SimpleNamespace(FOLDER=Path("runs/mock"), build=build)
    monkeypatch.setattr(FIGURE, "figures_module", lambda: figs)
    figure = FIGURE.Figure(
        "mock", "a stand-in", "build", "mock", ("FOLDER",), lambda f: [Path(run)]
    )
    return SimpleNamespace(figure=figure, run=Path(run), seen=seen)


def test_figure_commands_regenerate_estimates_and_asks_first(
    small_figure, monkeypatch, capsys
):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert FIGURE.regenerate(small_figure.figure, "regen") == 1
    out = capsys.readouterr().out
    assert "mock: 1 games, 0 model calls, at most $0.00 estimated." in out
    assert FIGURE.NEW_SAMPLE in out
    assert "Stopped before spending anything." in out
    assert not Path("regen").exists()


def test_figure_commands_regenerate_refuses_over_the_cap(small_figure, monkeypatch):
    monkeypatch.setattr(
        FIGURE,
        "plan",
        lambda figure, figs=None: FIGURE.Plan([], 10, 2.5, []),
    )
    assert FIGURE.regenerate(small_figure.figure, "regen", max_cost=1, yes=True) == 1
    assert not Path("regen").exists()


def test_figure_commands_regenerate_writes_apart(small_figure):
    before = {p: p.read_bytes() for p in small_figure.run.rglob("*") if p.is_file()}
    assert FIGURE.regenerate(small_figure.figure, "regen", yes=True) == 0
    again = Path("regen") / small_figure.run
    assert json.loads((again / "summary.json").read_text())["seed"] == 0
    assert small_figure.seen["folder"] == Path("regen/runs/mock")
    assert "regen/runs/mock" in Path("regen/figures/mock.svg").read_text()
    assert before == {
        p: p.read_bytes() for p in small_figure.run.rglob("*") if p.is_file()
    }
    assert FIGURE.regenerate(small_figure.figure, "regen", yes=True) == 0  # resumes


def test_figure_commands_paper_lines_match_the_registry():
    """The paper's table names each figure's commands and games as the
    registry has them; its costs were priced when written, so only their
    presence is checked offline."""
    text = FIGURE.PAPER.read_text()
    block = text[text.index(FIGURE.BEGIN) + len(FIGURE.BEGIN) : text.index(FIGURE.END)]
    figs = FIGURE.figures_module()
    expected = (
        [FIGURE.HEADER]
        + [FIGURE.row(f, len(list(f.runs(figs))), 0) for f in FIGURE.FIGURES.values()]
        + ["", FIGURE.CAPTION]
    )
    priced = re.sub(r"~\$\d+\.\d\d", "~$0.00", block.strip())
    assert priced == "\n".join(expected)


def test_figure_commands_regenerate_never_writes_over_what_is_committed(
    small_figure,
):
    assert FIGURE.regenerate(small_figure.figure, ".", yes=True) == 1
    assert FIGURE.regenerate(small_figure.figure, FIGURE.HERE, yes=True) == 1
    assert not (FIGURE.HERE / "figures" / "mock.svg").exists()


def test_figure_commands_regenerate_keeps_a_failed_runs_spend(
    small_figure, monkeypatch, provenance_index
):
    def fail(config, out, cache):
        played = Path(out) / "seed-0"
        played.mkdir(parents=True)
        (played / "manifest.json").write_text(json.dumps({"cost": 0.25}))
        raise FIGURE.RunFailed("spend cap passed")

    monkeypatch.setattr(FIGURE, "run_config", fail)
    assert FIGURE.regenerate(small_figure.figure, "regen", yes=True) == 1
    [line] = [json.loads(x) for x in provenance_index.read_text().splitlines()]
    assert line["spent"] == 0.25
    assert list(Path("regen", FIGURE.WORK).rglob("manifest.json"))  # resumable
