# Implements: ci/ci-minutes, ci/one-gate, ci/ci-runs-everything
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
    steps = " ".join(
        str(s.get("run", "")) for s in workflow()["jobs"]["blocking-checks"]["steps"]
    )
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


def test_ci_minutes_newer_runs_cancel_older_ones_and_drafts_wait():
    flow = workflow()
    assert flow["concurrency"]["cancel-in-progress"] is True
    assert "pull_request.number" in flow["concurrency"]["group"]
    assert "draft" in flow["jobs"]["blocking-checks"]["if"]
