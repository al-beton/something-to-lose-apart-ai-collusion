# Implements: tooling/quick-start, tooling/key-setup, tooling/how-tos, tooling/how-we-work
"""The README a newcomer follows: its commands, files and links are real."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()


def section(title):
    """The text of one `## title` section."""
    match = re.search(
        rf"^## {title}\n(.*?)(?=^## |\Z)", README, re.MULTILINE | re.DOTALL
    )
    assert match, f"README has no '## {title}' section."
    return match.group(1)


def test_quick_start_goes_from_clone_to_a_report_then_a_real_run():
    steps = section("Quick start")
    order = ["git clone", "make install", "mock/", "lab run", "lab report"]
    places = [steps.find(step) for step in order]
    assert -1 not in places and places == sorted(places), dict(
        zip(order, places, strict=True)
    )
    assert "openrouter/" in steps.split("lab report", 1)[1]


def test_key_setup_names_the_variable_spend_limit_and_no_sprint_credits():
    example = (ROOT / ".env.example").read_text()
    assert re.search(r"^OPENROUTER_API_KEY=$", example, re.MULTILINE)
    keys = section("Keys")
    assert "openrouter.ai/keys" in keys
    assert "limit" in keys
    assert "Modal" in keys and "no model credits" in keys
    assert ".env.example" in keys


def test_how_tos_name_files_and_spec_areas_that_exist():
    how = section("How to")
    for change in ["prompt", "model", "sweep", "market", "highlight", "experiment"]:
        assert change in how, change
    paths = re.findall(r"`((?:src|prompts|configs|experiments|product)/[^`]*?)`", how)
    links = re.findall(r"\]\(([^)#]+)\)", how)
    assert paths and links
    for path in paths + links:
        # Prompt names inside an agent's config, not files in the repository.
        if "<" in path:
            continue
        assert (ROOT / path).exists(), path


def test_how_we_work_is_five_lines_and_points_agents_to_agents_md():
    work = section("How we work")
    assert len(re.findall(r"^\d+\. ", work, re.MULTILINE)) == 5
    assert "AGENTS.md" in work
