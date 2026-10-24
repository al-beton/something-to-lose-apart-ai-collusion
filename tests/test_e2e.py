# Implements: ci/end-to-end
"""The whole path, as a person runs it: `lab run`, then `lab summary` and `lab report`.

Each command runs as its own process, from an empty folder with no API keys in
its environment, so only free scripted agents can play. `make e2e` runs this file.
"""

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

CONFIG = """
name: e2e
seeds: [0, 1]
market: {rounds: 6, talk: true}
summary: {last_rounds: 3}
agents:
  - {id: A, model: mock/nash, prompt: system/neutral.md}
  - {id: B, model: mock/nash, prompt: system/neutral.md}
sweep:
  agents.*.model: [mock/nash, mock/joint, mock/proposer]
"""

ARMS = ["mock-nash", "mock-joint", "mock-proposer"]
SECTIONS = ["header", "summary", "setup", "charts", "arms"]
PROMPTS = Path(__file__).resolve().parents[1] / "prompts"


def lab(*args, cwd):
    """Run the installed `lab` command; fail the test with its output if it fails."""
    command = Path(sys.executable).with_name("lab")
    env = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
    done = subprocess.run(
        [str(command), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    return done.stdout


@pytest.fixture(scope="module")
def played(tmp_path_factory):
    """One small sweep, its summary table and its report, built once."""
    work = tmp_path_factory.mktemp("e2e")
    (work / "prompts").symlink_to(PROMPTS)
    (work / "e2e.yaml").write_text(textwrap.dedent(CONFIG))
    printed = lab("run", "e2e.yaml", "--out", "runs", "--cache", "off", cwd=work)
    table = lab("summary", "runs", cwd=work)
    page = Path(lab("report", "runs", cwd=work).strip())
    if not page.is_absolute():
        page = work / page
    return work / "runs" / "e2e", printed, table, page.read_text()


def rows(table):
    """The summary table's rows, keyed by the swept model."""
    lines = [
        [cell.strip() for cell in line.strip("|").split("|")]
        for line in table.strip().splitlines()
    ]
    header = lines[0]
    return {cells[0]: dict(zip(header, cells, strict=True)) for cells in lines[2:]}


def test_end_to_end_plays_every_arm_and_seed_into_its_own_folder(played):
    runs, printed, _, _ = played
    for arm in ARMS:
        for seed in (0, 1):
            folder = runs / f"model={arm}" / f"seed-{seed}"
            assert f"runs/e2e/model={arm}/seed-{seed}" in printed.splitlines()
            for name in ("config.yaml", "manifest.json", "summary.json", "turns.jsonl"):
                assert (folder / name).is_file(), folder / name
            manifest = json.loads((folder / "manifest.json").read_text())
            assert manifest  # written and readable


def test_end_to_end_summary_numbers_make_sense(played):
    _, _, table, _ = played
    found = rows(table)
    assert found["mock/nash"]["mean price"] == "6"
    assert float(found["mock/nash"]["gain"]) == 0
    assert found["mock/joint"]["mean price"] == "9"
    assert float(found["mock/joint"]["gain"]) == 1
    assert all(row["runs"] == "2" for row in found.values())
    assert all(row["cost"] == "0" for row in found.values())


def test_end_to_end_report_has_every_section_and_highlights(played):
    _, _, _, html = played
    for section in SECTIONS:
        assert f'<section id="{section}"' in html, section
    kinds = set(re.findall(r'class="highlight" data-kind="([a-z]+)"', html))
    assert {"proposal", "agreement", "defection"} <= kinds, kinds
