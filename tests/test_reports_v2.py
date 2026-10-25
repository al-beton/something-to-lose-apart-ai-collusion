# Implements: reports/many-folders, reports/premium-chart, reports/disclosure-chart, reports/written-summary, reports/picked-highlights
import json
import re

import pytest
import yaml

from collusion_lab import cli, prices
from collusion_lab.cache import Cache
from collusion_lab.report import build_report
from collusion_lab.report.written import (
    ai_highlights,
    ai_summary,
    hand_highlights,
    hand_summary,
)
from collusion_lab.runner import run_config

MODEL = "openrouter/openai/gpt-4.1-mini"


def section(html, name):
    match = re.search(rf'<section id="{name}">(.*?)</section>', html, re.DOTALL)
    return match.group(1) if match else ""


@pytest.fixture
def folders(make_config, tmp_path):
    """Two folders: a cartel (both firms at the joint-profit price) and a
    competitive pair, each a one-value sweep over the model."""
    made = []
    for name, model in (("cartel", "mock/joint"), ("rivals", "mock/nash")):
        sweep = f"sweep={{agents.*.model: [{model}]}}"
        run_config(make_config(overrides=[sweep, f"name={name}"]), tmp_path / name)
        made.append(tmp_path / name)
    return made


def test_many_folders_make_one_report(folders):
    html = build_report(folders)
    summary = section(html, "summary")
    assert "mock/joint" in summary and "mock/nash" in summary
    assert html.count('class="game"') == 2


def test_premium_chart_places_each_arm_between_nash_and_joint(folders):
    chart = section(build_report(folders), "premium")
    assert 'class="chart premium"' in chart
    values = dict(re.findall(r"<title>([^<]+): premium ([\d.-]+)</title>", chart))
    assert values == {"cartel, joint": "1.00", "rivals, nash": "0.00"}


def test_disclosure_chart_only_when_audited(make_config, tmp_path, folders, fake_model):
    assert section(build_report(folders), "disclosure") == ""
    audited = make_config(
        overrides=[
            "conditions={audit: {enabled: true, round: 2}}",
            "name=audited",
            f"agents.0.model={MODEL}",  # scripted firms aren't counted
        ]
    )
    run_config(audited, tmp_path / "audited")
    chart = section(build_report(tmp_path / "audited"), "disclosure")
    assert "honest disclosure" in chart and "denials" in chart


def test_written_summary_by_hand_or_ai_labelled(folders, tmp_path, fake_model):
    note = tmp_path / "note.md"
    note.write_text("Cartels form when nobody stops them.\n")
    html = build_report(folders, summary=hand_summary(note))
    assert "Cartels form when nobody stops them." in section(html, "written")
    assert "Written by hand" in section(html, "written")
    fake_model.replies = ["The joint arm colludes fully; the Nash arm competes."]
    cache = Cache(tmp_path / "cache.sqlite")
    made = ai_summary(folders, MODEL, cache)
    html = build_report(folders, summary=made)
    assert "The joint arm colludes fully" in section(html, "written")
    assert "AI-written" in section(html, "written") and MODEL in section(
        html, "written"
    )
    assert ai_summary(folders, MODEL, cache) == made and len(fake_model.calls) == 1


def test_picked_highlights_by_hand_or_ai_labelled(folders, tmp_path, fake_model):
    run = json.loads(next(folders[0].rglob("summary.json")).read_text())["run"]
    picks = tmp_path / "picks.yaml"
    picks.write_text(
        yaml.safe_dump(
            [
                {
                    "run": f"runs/x/{run}",
                    "round": 2,
                    "firm": "A",
                    "note": "Holds 9 again.",
                }
            ]
        )
    )
    html = build_report(folders, highlights=hand_highlights(picks))
    picked = section(html, "picked")
    assert "Holds 9 again." in picked and "Picked by hand" in picked
    assert "Round 2" in picked and "<details" in picked
    reply = [{"run": run, "round": 3, "firm": "B", "note": "Never budges."}]
    fake_model.replies = [json.dumps(reply)]
    made = ai_highlights(folders, MODEL, Cache(tmp_path / "cache.sqlite"))
    picked = section(build_report(folders, highlights=made), "picked")
    assert "Never budges." in picked and "Picked by AI" in picked


def test_report_command_takes_folders_and_a_summary(folders, tmp_path, capsys):
    note = tmp_path / "note.md"
    note.write_text("By hand.\n")
    out = tmp_path / "both.html"
    args = ["report", str(folders[0]), str(folders[1]), "--summary", str(note)]
    assert cli.main([*args, "--out", str(out)]) == 0
    html = out.read_text()
    assert "By hand." in html and "mock/nash" in html


def test_compact_runs_make_a_report(folders, tmp_path):
    import shutil
    import subprocess
    import sys

    committed = tmp_path / "committed"
    for run in folders[0].rglob("turns.jsonl"):
        keep = committed / run.parent.relative_to(folders[0])
        keep.mkdir(parents=True)
        for name in ("config.yaml", "summary.json", "manifest.json"):
            shutil.copy(run.parent / name, keep / name)
    subprocess.run(
        [sys.executable, "reports/compact_turns.py", str(folders[0]), str(committed)],
        check=True,
    )
    assert not list(committed.rglob("turns.jsonl"))
    html = build_report(committed)
    assert 'class="game"' in html and "mock/joint" in html


def test_many_folders_keep_the_same_settings_apart(make_config, tmp_path):
    for name in ("first", "second"):
        sweep = "sweep={agents.*.model: [mock/joint]}"
        run_config(make_config(overrides=[sweep, f"name={name}"]), tmp_path / name)
    html = build_report([tmp_path / "first", tmp_path / "second"])
    summary = section(html, "summary")
    assert "first" in summary and "second" in summary
    assert html.count('name="arm"') == 2  # one tab per folder


def test_report_asks_before_an_ai_summary(
    folders, tmp_path, capsys, monkeypatch, fake_model
):
    monkeypatch.chdir(tmp_path)  # a fresh cache, so the call isn't already cached
    monkeypatch.setattr(prices, "_openrouter_prices", dict)  # stay offline
    answers = iter(["n", "y"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    args = ["report", str(folders[0]), "--ai-summary", "--out", "r.html"]
    assert cli.main(args) == 1
    out = capsys.readouterr().out
    assert MODEL in out and "1 call" in out and "estimated" in out
    assert not fake_model.calls and not (tmp_path / "r.html").exists()
    assert cli.main(args) == 0 and len(fake_model.calls) == 1
    assert cli.main([*args, "-y"]) == 0  # cached now, no question asked


def test_picked_highlights_find_the_right_folder(make_config, tmp_path):
    """Two folders hold the same run id; a pick naming the second shows the
    second's round, not the first's."""
    for name, model in (("first", "mock/joint"), ("second", "mock/nash")):
        overrides = [f"agents.0.model={model}", f"agents.1.model={model}"]
        run_config(make_config(overrides=overrides), tmp_path / name)
    [second] = [p.parent for p in (tmp_path / "second").rglob("summary.json")]
    picks = tmp_path / "picks.yaml"
    picks.write_text(
        yaml.safe_dump([{"run": str(second), "round": 2, "firm": "A", "note": "x"}])
    )
    html = build_report(
        [tmp_path / "first", tmp_path / "second"],
        highlights=hand_highlights(picks),
    )
    picked = section(html, "picked")
    assert "<td>6</td>" in picked and "<td>9</td>" not in picked  # Nash, not joint
    assert "second" in picked
