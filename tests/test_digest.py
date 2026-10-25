# Implements: runs/digest, ci/results-digest, ci/numbers-checked
import subprocess

import yaml

from collusion_lab import cli, digest
from collusion_lab.runner import run_config

MOMENT = {
    "label": "holds-nine",
    "model": "mock/joint",
    "run": "runs/joint/test/seed-0",
    "round": 1,
    "phase": "talk",
    "firm": "A",
    "field": "message",
    "quote": "Hold at 9.",
}


def repo(make_config, tmp_path):
    """A repository holding two experiments of mock firms, a registry, a note
    and a moment, committed."""
    for model in ("joint", "nash"):
        overrides = [f"agents.0.model=mock/{model}", f"agents.1.model=mock/{model}"]
        run_config(make_config(overrides=overrides), tmp_path / "runs" / model)
    reports = tmp_path / "reports"
    reports.mkdir()
    experiments = [
        {"name": "joint", "runs": ["runs/joint"], "note": "reports/joint.md"},
        {"name": "nash", "runs": ["runs/nash"], "rounds": "1-2"},
    ]
    (reports / "experiments.yaml").write_text(yaml.safe_dump(experiments))
    (reports / "joint.md").write_text("Joint pricing.\n")
    (reports / "moments.yaml").write_text(yaml.safe_dump([MOMENT]))
    git = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run([*git, "commit", "-q", "-m", "base"], cwd=tmp_path, check=True)
    return tmp_path, experiments


def test_digest_reads_the_registry(make_config, tmp_path):
    root, _ = repo(make_config, tmp_path)
    experiments = digest.registry(root / "reports" / "experiments.yaml")
    page = digest.digest(experiments, root)
    assert page.startswith("## Results digest")
    assert "| joint | 1 | 1 | +1.00 to +1.00 | last rounds |" in page
    assert "| nash | 1 | 1 | +0.00 to +0.00 | 1-2 |" in page
    assert page.count("<details>") == 2 and "```mermaid\nxychart-beta" in page
    assert "`[" + " " * 20 + "•]`" in page  # the joint game's strip
    assert "> Hold at 9." in page and "Findings: [`reports/joint.md`]" in page


def test_digest_changed_only(make_config, tmp_path, monkeypatch, capsys):
    root, experiments = repo(make_config, tmp_path)
    assert digest.changed(experiments, "HEAD", root) == []
    (root / "reports" / "joint.md").write_text("Joint pricing, revised.\n")
    git = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*git, "commit", "-qam", "note"], cwd=root, check=True)
    assert [e["name"] for e in digest.changed(experiments, "HEAD~1", root)] == ["joint"]
    # A change to the code that computes results digests the sample too.
    sample = [experiments[0], experiments[1] | {"sample": True}]
    charts = root / "src" / "collusion_lab" / "charts.py"
    charts.parent.mkdir(parents=True)
    charts.write_text("# changed\n")
    subprocess.run(["git", "add", "src"], cwd=root, check=True)
    subprocess.run([*git, "commit", "-qm", "code"], cwd=root, check=True)
    assert [e["name"] for e in digest.changed(sample, "HEAD~1", root)] == ["nash"]
    # Nothing changed: the command prints nothing, so CI posts no section.
    monkeypatch.setattr(digest, "REGISTRY", root / "reports" / "experiments.yaml")
    monkeypatch.setattr(digest, "ROOT", root)
    assert cli.main(["digest", "--changed-only", "--since", "HEAD"]) == 0
    assert capsys.readouterr().out == ""


def test_numbers_checked_against_the_runs(make_config, tmp_path, monkeypatch, capsys):
    root, experiments = repo(make_config, tmp_path)
    note = root / "reports" / "joint.md"
    cell = "all"
    note.write_text(f"Gain is 1.<!-- check: {cell} | gain = 1.0 -->\n")
    assert digest.check(experiments, root) == []
    note.write_text(f"Gain is 0.9.<!-- check: {cell} | gain = 0.9 -->\n")
    [problem] = digest.check(experiments, root)
    assert "gain is 1.0, the note says 0.9" in problem
    note.write_text("<!-- check: nobody | gain = 1.0 -->\n")
    assert "no cell 'nobody'" in digest.check(experiments, root)[0]
    monkeypatch.setattr(digest, "REGISTRY", root / "reports" / "experiments.yaml")
    monkeypatch.setattr(digest, "ROOT", root)
    assert cli.main(["digest", "--check"]) == 1
    assert "no cell 'nobody'" in capsys.readouterr().err


def test_results_digest_fits_a_comment(make_config, tmp_path, monkeypatch):
    root, experiments = repo(make_config, tmp_path)
    monkeypatch.setattr(digest, "LIMIT", 800)
    page = digest.digest(experiments, root)
    assert len(page) <= 800 + 200
    assert "were cut to fit a comment" in page


def test_digest_names_cells_by_folder_when_there_are_several(make_config, tmp_path):
    """Two folders of the same cells (a control and a treatment) stay apart."""
    root, _ = repo(make_config, tmp_path)
    both = {"name": "both", "runs": ["runs/joint", "runs/nash"]}
    cells = [r["cell"] for r in digest.rows_of(both, root)]
    assert cells == ["joint / all", "nash / all"]
