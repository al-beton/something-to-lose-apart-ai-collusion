# Implements: ci/ci-minutes, ci/one-gate, ci/ci-runs-everything
import re
import subprocess
from pathlib import Path

import yaml

WORKFLOWS = Path(".github/workflows")


def workflow():
    return yaml.safe_load((WORKFLOWS / "blocking-checks.yml").read_text())


def test_ci_minutes_one_job_named_like_the_gate():
    # Every check is a step of one job, billed as one minute, and its name is
    # the status deliver.py's merge waits for.
    assert list(workflow()["jobs"]) == ["blocking-checks"]
    assert [p.name for p in WORKFLOWS.glob("*.yml")] == ["blocking-checks.yml"]


def test_ci_minutes_one_job_runs_every_check():
    runs = [
        str(s["run"])
        for s in workflow()["jobs"]["blocking-checks"]["steps"]
        if "run" in s
    ]
    steps = " ".join(runs)
    for check in (
        "pr_gate.py",
        "make lint",
        "make test",
        "make spec-check",
        "lab run configs/pr-game.yaml",
        "lab report",
        "report_comment.py",
    ):
        assert check in steps, check
    # Each step runs something that exists: a Makefile target make knows, and
    # the scripts and config the steps name.
    for run in runs:
        if run.startswith("make "):
            target = run.split()[1]
            dry = subprocess.run(
                ["make", "-n", target], capture_output=True, text=True, check=False
            )
            assert dry.returncode == 0, f"{run}: {dry.stderr}"
    for path in re.findall(r"[\w./-]+\.(?:py|yaml)", steps):
        assert Path(path).is_file(), path


def test_ci_minutes_newer_runs_cancel_older_ones_and_drafts_wait():
    flow = workflow()
    # Only pull request runs cancel: main's runs after a merge must finish,
    # or a second merge would make the first look as if main failed.
    cancel = flow["concurrency"]["cancel-in-progress"]
    assert cancel == "${{ github.event_name == 'pull_request' }}"
    assert "pull_request.number || github.run_id" in flow["concurrency"]["group"]
    assert "draft" in flow["jobs"]["blocking-checks"]["if"]
