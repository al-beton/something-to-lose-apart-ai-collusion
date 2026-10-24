# Implements: agents/prompt-templates, agents/stance-prompts
from pathlib import Path

import pytest

from collusion_lab.prompts import PromptError, render


def test_prompt_templates_fill_placeholders_and_keep_the_rest_verbatim(tmp_path):
    (tmp_path / "p.md").write_text('You are $me.\nReply {"price": <n>}  \n')
    assert render(tmp_path, "p.md", {"me": "Firm A"}) == (
        'You are Firm A.\nReply {"price": <n>}  \n'
    )


def test_prompt_templates_stop_on_unknown_placeholders(tmp_path):
    (tmp_path / "p.md").write_text("You are $whom.\n")
    with pytest.raises(PromptError, match="whom"):
        render(tmp_path, "p.md", {"me": "Firm A"})


def test_prompt_templates_shipped_render_for_every_phase():
    from collusion_lab.runner import (
        OWN_PRICE_PROMPT,
        PHASE_PROMPTS,
        prompt_vars_example,
    )

    root = Path("prompts")
    system = [
        p.relative_to(root).as_posix() for p in sorted(root.rglob("system/**/*.md"))
    ]
    assert {"system/fiduciary.md", "system/stakes/owned-1.md"} <= set(system)
    for name in [*system, *PHASE_PROMPTS.values(), OWN_PRICE_PROMPT]:
        assert "$" not in render("prompts", name, prompt_vars_example())


def test_stance_prompts_fiduciary_says_nothing_about_collusion():
    for name in ("fiduciary.md", "fiduciary-alt.md"):
        text = Path("prompts/system", name).read_text().lower()
        assert "$me" in text
        for word in ("collu", "coordinat", "competition law", "cartel", "agree"):
            assert word not in text, (name, word)
    assert "collude" in Path("prompts/system/no-collusion.md").read_text()


STAKES = Path("prompts/system/stakes")
ARMS = ["fiduciary", "illegal", "instruction", "termination", "owned"]


def test_stakes_prompts_build_on_the_fiduciary_job():
    base = Path("prompts/system/fiduciary.md").read_text().strip()
    alt = Path("prompts/system/fiduciary-alt.md").read_text().strip()
    for arm in ARMS:
        assert (STAKES / f"{arm}-1.md").read_text().startswith(base)
        assert (STAKES / f"{arm}-2.md").read_text().startswith(alt)
    added = {
        arm: (STAKES / f"{arm}-1.md").read_text().removeprefix(base).lower()
        for arm in ARMS
    }
    assert added["fiduciary"].strip() == ""
    assert "illegal" in added["illegal"] and "collude" not in added["illegal"]
    assert "must not collude" in added["instruction"]
    assert "terminated" in added["termination"] and "illegal" in added["termination"]
    for words in ("1,000 credits", "60 credits", "600 credits", "yours"):
        assert words in added["owned"]


def test_stakes_prompts_sweep_five_arms():
    from collusion_lab.config import expand, load_config

    config = load_config("configs/stakes.yaml")
    assert config.market.c == 1.8
    arms = [child.agents[0].prompt for child in expand(config)]
    assert arms == [f"system/stakes/{arm}-1.md" for arm in ARMS]
