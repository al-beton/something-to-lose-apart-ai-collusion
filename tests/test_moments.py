# Implements: reports/moments-cited
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path("reports/check_moments.py")
HEADER = "| label | model | run | round | phase | firm | quote |\n|---|---|---|---|---|---|---|\n"


def load():
    spec = importlib.util.spec_from_file_location("check_moments", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def repo(tmp_path):
    run = tmp_path / "runs" / "pilot" / "seed-0"
    run.mkdir(parents=True)
    turns = [
        {
            "round": 8,
            "phase": "talk",
            "agent": "B",
            "used": {"message": "Hold at 9."},
            "scratchpad": "This notice is   Suspicious, maybe a trap.",
        },
        {
            "round": 10,
            "phase": "audit",
            "agent": "A",
            "used": {"answer": "No, we never agreed anything.", "admits": False},
            "scratchpad": None,
        },
    ]
    (run / "turns.compact.jsonl").write_text(
        "".join(json.dumps(t) + "\n" for t in turns)
    )
    return tmp_path


def index(repo, *rows):
    path = repo / "moments.md"
    path.write_text("# Moments\n\n" + HEADER + "".join(rows))
    return path


def test_moments_cited_found_in_scratchpad_and_answer(repo):
    path = index(
        repo,
        "| outage-suspicious | deepseek | `runs/pilot/seed-0` | 8 | talk | B | `notice is suspicious` |\n",
        "| deny | haiku | `runs/pilot/seed-0` | 10 | audit | A | `we never agreed` |\n",
    )
    assert load().check(path, repo) == []


@pytest.mark.parametrize(
    ("row", "problem"),
    [
        ("| x | m | `runs/missing` | 8 | talk | B | `hold` |\n", "no run"),
        ("| x | m | `runs/pilot/seed-0` | 9 | talk | B | `hold` |\n", "no turn"),
        ("| x | m | `runs/pilot/seed-0` | 8 | talk | A | `hold` |\n", "no turn"),
        ("| x | m | `runs/pilot/seed-0` | 8 | talk | B | `hold at 10` |\n", "quote"),
        ("| x | m | `runs/pilot/seed-0` | eight | talk | B | `hold` |\n", "round"),
    ],
)
def test_moments_cited_fails_on_what_the_logs_dont_hold(repo, row, problem):
    [error] = load().check(index(repo, row), repo)
    assert problem in error and "line" in error


def test_moments_cited_from_the_command_line(repo, capsys):
    path = index(repo, "| x | m | `runs/pilot/seed-0` | 8 | talk | B | `nope` |\n")
    assert load().main([str(path), "--root", str(repo)]) == 1
    assert "quote" in capsys.readouterr().err


def test_moments_cited_in_the_repositorys_own_index():
    path = Path("reports/moments.md")
    if not path.exists():
        pytest.skip("no index committed yet")
    assert load().check(path, Path(".")) == []
