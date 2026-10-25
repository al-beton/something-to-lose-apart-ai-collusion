# Implements: runs/fork-pointers
import importlib.util
import json
import re
import shutil
from pathlib import Path

from collusion_lab import backends, forks
from collusion_lab.analysis import turn_lines
from collusion_lab.report import load_game
from collusion_lab.runner import run_config


def script(name):
    spec = importlib.util.spec_from_file_location(name, f"reports/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def forked(make_config, tmp_path, monkeypatch, fake_model):
    """Two arms of one seed that differ only from the round-4 audit on (the
    stated chance of being caught, which firm A's answer quotes), committed
    as compact runs: (base, fork, their original compact logs)."""

    async def reply(**kwargs):
        prompt = kwargs["messages"][-1]["content"]
        if "compliance auditor" in prompt:
            chance = re.search(r"(\d+)% chance", prompt)[1]
            text = json.dumps({"answer": f"No ({chance}%).", "admits": False})
        else:
            text = json.dumps(
                {"price": 7} if "set your price" in prompt else {"message": "hi"}
            )
        fake_model.replies = [text]
        return await fake_model(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", reply)
    for arm, chance in (("sure", 100), ("unlikely", 10)):
        audit = {"enabled": True, "round": 4, "detection": chance}
        overrides = [
            f"conditions={json.dumps({'audit': audit})}",
            "agents.0.model=openai/gpt-4.1-mini",
        ]
        run_config(make_config(overrides=overrides), tmp_path / "full" / arm)
    script("compact_turns").main(tmp_path / "full", tmp_path / "committed")
    runs = []
    for arm in ("sure", "unlikely"):  # path order: the base first
        [log] = (tmp_path / "full" / arm).rglob("turns.jsonl")
        run = tmp_path / "committed" / log.parent.relative_to(tmp_path / "full")
        for name in ("summary.json", "manifest.json", "config.yaml"):
            shutil.copy(log.parent / name, run / name)
        runs.append(run)
    originals = [(r / forks.COMPACT).read_text() for r in runs]
    return *runs, originals


def test_fork_pointers_rebuild_byte_for_byte(
    make_config, tmp_path, monkeypatch, fake_model
):
    base, fork, (base_log, fork_log) = forked(
        make_config, tmp_path, monkeypatch, fake_model
    )
    assert script("pack_forks").main(tmp_path / "committed") == 0
    assert not (base / forks.POINTER).exists()  # the base stays whole
    pointer = json.loads((fork / forks.POINTER).read_text())
    assert (fork / pointer["base"]).resolve() == base.resolve()
    assert pointer["round"] == 4  # its own turns start at the audit
    own = (fork / forks.COMPACT).read_text()
    assert len(own) < len(fork_log) / 2
    assert forks.compact_text(fork) == fork_log
    assert forks.compact_text(base) == base_log
    # Again, nothing changes.
    assert script("pack_forks").main(tmp_path / "committed") == 0
    assert (fork / forks.COMPACT).read_text() == own


def test_fork_pointers_leave_a_differing_run_alone(
    make_config, tmp_path, monkeypatch, fake_model
):
    base, fork, (_, fork_log) = forked(make_config, tmp_path, monkeypatch, fake_model)
    lines = forks.shared(base, fork)
    # One line more than they share would rebuild a different log.
    assert forks.pack(base, fork, lines + 1) is False
    assert (fork / forks.COMPACT).read_text() == fork_log
    assert not (fork / forks.POINTER).exists()


def test_fork_pointers_every_reader_sees_the_whole_game(
    make_config, tmp_path, monkeypatch, fake_model
):
    _, fork, (_, fork_log) = forked(make_config, tmp_path, monkeypatch, fake_model)
    before = load_game(fork)
    script("pack_forks").main(tmp_path / "committed")
    after = load_game(fork)
    assert [r.prices for r in after.rounds] == [r.prices for r in before.rounds]
    assert len(after.rounds[3].audit) == 2
    whole = [json.loads(line) for line in fork_log.splitlines()]
    assert turn_lines(fork) == whole
    assert script("check_moments")._turns(fork) == whole


def test_fork_pointers_e9_numbers_unchanged():
    """Every E9 number reads the same, packed or not: the pinned outputs of
    reports/e9/analyse.py and `lab analyse runs/e9` (test_analysis_shared)
    were taken before E9 was packed."""
    packed = list(Path("runs/e9").rglob(forks.POINTER))
    assert packed  # E9 is committed packed
    for pointer in packed[:50]:
        run = pointer.parent
        assert forks.compact_lines(run)[0].startswith('{"round": 0')


def test_fork_pointers_dropped_when_a_whole_log_is_written_again(
    make_config, tmp_path, monkeypatch, fake_model
):
    """Compacting the full logs over a packed folder again writes whole logs
    and removes their pointers, so no turn is read twice."""
    _, fork, (_, fork_log) = forked(make_config, tmp_path, monkeypatch, fake_model)
    script("pack_forks").main(tmp_path / "committed")
    assert (fork / forks.POINTER).exists()
    script("compact_turns").main(tmp_path / "full", tmp_path / "committed")
    assert not (fork / forks.POINTER).exists()
    assert forks.compact_text(fork) == fork_log
