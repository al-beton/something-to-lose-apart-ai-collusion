# Implements: reports/moments-cited
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

SCRIPT = Path("reports/check_moments.py")
RUN = "runs/pilot/seed-0"


def load():
    spec = importlib.util.spec_from_file_location("check_moments", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def repo(tmp_path):
    run = tmp_path / RUN
    run.mkdir(parents=True)
    turns = [
        {
            "round": 8,
            "phase": "talk",
            "agent": "B",
            "used": {"message": "Hold at 9."},
            "scratchpad": "This notice is   suspicious, maybe a trap.",
        },
        {
            "round": 10,
            "phase": "audit",
            "agent": "A",
            "used": {"answer": "No, we never agreed anything.", "admits": False},
            "scratchpad": None,
        },
        {
            "round": 4,
            "phase": "price",
            "agent": "B",
            "used": {"price": 9},
            "scratchpad": None,
            "reasoning": "Tacit parallel   pricing is fine legally.",
        },
    ]
    (run / "turns.compact.jsonl").write_text(
        "".join(json.dumps(t) + "\n" for t in turns)
    )
    config = {
        "agents": [{"id": "A", "model": "m/alpha"}, {"id": "B", "model": "m/beta"}]
    }
    (run / "config.yaml").write_text(yaml.safe_dump(config))
    return tmp_path


def moment(**changes):
    base = {
        "label": "outage-suspicious",
        "model": "m/beta",
        "run": RUN,
        "round": 8,
        "phase": "talk",
        "firm": "B",
        "field": "scratchpad",
        "quote": "notice is suspicious",
    }
    return base | changes


def index(repo, *moments):
    path = repo / "moments.yaml"
    path.write_text(yaml.safe_dump(list(moments)))
    return path


def test_moments_cited_found_in_the_named_field(repo):
    path = index(
        repo,
        moment(),
        moment(label="hold", field="message", quote="Hold at 9."),
        moment(
            label="deny",
            model="m/alpha",
            round=10,
            phase="audit",
            firm="A",
            field="answer",
            quote="we never agreed",
        ),
    )
    assert load().check(path, repo) == []


@pytest.mark.parametrize(
    ("changes", "problem"),
    [
        ({"run": "runs/missing"}, "no run"),
        ({"round": 9}, "no turn"),
        ({"firm": "A"}, "no turn"),
        ({"quote": "notice is Suspicious"}, "quote"),
        ({"field": "message"}, "quote"),
        ({"field": "reasoning"}, "quote"),  # this turn has no reasoning
        ({"field": "notes"}, "field"),
        ({"model": "m/alpha"}, "model"),
        ({"round": "eight"}, "round"),
    ],
)
def test_moments_cited_fails_on_what_the_logs_dont_hold(repo, changes, problem):
    [error] = load().check(index(repo, moment(**changes)), repo)
    assert problem in error and "outage-suspicious" in error


def test_moments_cited_from_native_reasoning(repo):
    """A no-scratchpad turn's telling text is the provider's reasoning."""
    cited = moment(
        label="tacit-is-legal",
        round=4,
        phase="price",
        field="reasoning",
        quote="Tacit parallel pricing is fine legally.",
    )
    assert load().check(index(repo, cited), repo) == []
    wrong = cited | {"quote": "explicit pricing"}
    assert "isn't in that turn's reasoning" in load().check(index(repo, wrong), repo)[0]


def test_moments_cited_from_the_command_line(repo, capsys):
    path = index(repo, moment(quote="nope"))
    assert load().main([str(path), "--root", str(repo)]) == 1
    assert "quote" in capsys.readouterr().err


def test_moments_cited_in_the_repositorys_own_index():
    path = Path("reports/moments.yaml")
    if not path.exists():
        pytest.skip("no index committed yet")
    assert load().check(path, Path(".")) == []
