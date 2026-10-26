# Implements: ci/ci-minutes, ci/one-gate, ci/ci-runs-everything, ci/no-model-calls, ci/paper-preview
import re
import subprocess
from pathlib import Path

import yaml

WORKFLOWS = Path(".github/workflows")


def workflow():
    return yaml.safe_load((WORKFLOWS / "blocking-checks.yml").read_text())


def runs(job=None):
    """The `run` lines of one job of the gate's workflow, or of every job."""
    jobs = workflow()["jobs"]
    return [
        str(s["run"])
        for name in ([job] if job else jobs)
        for s in jobs[name]["steps"]
        if "run" in s
    ]


def test_ci_minutes_the_gate_is_one_job_and_the_report_runs_beside_it():
    # Every gating check is a step of one job, whose name is the status
    # deliver.py's merge waits for; the report job needs nothing from it.
    jobs = workflow()["jobs"]
    assert list(jobs) == ["blocking-checks", "pr-report"]
    assert "needs" not in jobs["pr-report"] and "needs" not in jobs["blocking-checks"]
    # The paper preview is its own workflow and never gates a merge.
    assert sorted(p.name for p in WORKFLOWS.glob("*.yml")) == [
        "blocking-checks.yml",
        "paper-preview.yml",
    ]


def test_ci_minutes_tests_run_in_parallel_with_cached_dependencies():
    assert "pytest -n auto" in Path("Makefile").read_text()
    for job in workflow()["jobs"].values():
        uv = next(s for s in job["steps"] if "setup-uv" in s.get("uses", ""))
        assert uv["with"]["enable-cache"] is True


def test_ci_minutes_the_gate_runs_every_check():
    gate = " ".join(runs("blocking-checks"))
    for check in ("pr_gate.py", "make lint", "make test", "make spec-check", "--check"):
        assert check in gate, check
    report = " ".join(runs("pr-report"))
    for step in ("lab run configs/pr-game.yaml", "lab report", "report_comment.py"):
        assert step in report, step
    # Each step runs something that exists: a Makefile target make knows, and
    # the scripts and config the steps name.
    for run in runs():
        if run.startswith("make "):
            target = run.split()[1]
            dry = subprocess.run(
                ["make", "-n", target], capture_output=True, text=True, check=False
            )
            assert dry.returncode == 0, f"{run}: {dry.stderr}"
    for path in re.findall(r"[\w./-]+\.(?:py|yaml)", " ".join(runs())):
        assert Path(path).is_file(), path


def test_ci_minutes_newer_runs_cancel_older_ones_and_drafts_wait():
    flow = workflow()
    # Only pull request runs cancel: main's runs after a merge must finish,
    # or a second merge would make the first look as if main failed.
    cancel = flow["concurrency"]["cancel-in-progress"]
    assert cancel == "${{ github.event_name == 'pull_request' }}"
    assert "pull_request.number || github.run_id" in flow["concurrency"]["group"]
    for job in flow["jobs"].values():
        assert "draft" in job["if"]


def test_no_model_calls_in_any_config_ci_plays():
    """Every config CI plays (the workflow's `lab run`s, the end-to-end
    sweep) uses only scripted `mock/` agents."""
    steps = " ".join(runs())
    played = re.findall(r"lab run ([\w./-]+\.yaml)", steps)
    assert played  # the PR game at least
    e2e = Path(__file__).with_name("test_e2e.py").read_text()
    sweep = e2e.split('CONFIG = """', 1)[1].split('"""', 1)[0]  # make test plays it

    configs = [yaml.safe_load(Path(p).read_text()) for p in played]
    configs.append(yaml.safe_load(sweep))
    for config in configs:
        models = [a["model"] for a in config["agents"]]
        for arm in config.get("sweep", {}).values():
            models += [v for v in arm if isinstance(v, str) and "/" in v]
        assert all(m.startswith("mock/") for m in models), models


def test_no_model_calls_no_secret_but_the_github_token():
    """No workflow reads an API key: the only secret is the GitHub token."""
    for path in WORKFLOWS.glob("*.yml"):
        secrets = set(re.findall(r"secrets\.(\w+)", path.read_text()))
        assert secrets <= {"GITHUB_TOKEN"}, (path, secrets)


def test_paper_preview_builds_publishes_and_comments():
    flow = yaml.safe_load((WORKFLOWS / "paper-preview.yml").read_text())
    on = flow[True]  # YAML reads the key "on" as True
    assert "paper/**" in on["pull_request"]["paths"]
    assert "ready_for_review" in on["pull_request"]["types"]
    (job,) = flow["jobs"].values()
    assert "if" not in job  # drafts are built too
    runs = " ".join(str(s.get("run", "")) for s in job["steps"])
    assert "make -s paper-html paper-pdf" in runs
    assert "gh-pages" in runs and "<!-- paper-preview -->" in runs
    for link in ("paper.html", "paper.pdf"):
        assert link in runs, link
    assert "PATCH" in runs  # one comment, edited in place
