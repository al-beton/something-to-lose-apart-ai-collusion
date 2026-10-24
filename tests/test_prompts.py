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
    from collusion_lab.runner import PHASE_PROMPTS, prompt_vars_example

    system = [f"system/{p.name}" for p in sorted(Path("prompts/system").glob("*.md"))]
    assert {"system/fiduciary.md", "system/no-collusion.md"} <= set(system)
    for name in [*system, *PHASE_PROMPTS.values()]:
        assert "$" not in render("prompts", name, prompt_vars_example())


def test_stance_prompts_fiduciary_says_nothing_about_collusion():
    for name in ("fiduciary.md", "fiduciary-alt.md"):
        text = Path("prompts/system", name).read_text().lower()
        assert "$me" in text
        for word in ("collu", "coordinat", "competition law", "cartel", "agree"):
            assert word not in text, (name, word)
    assert "collude" in Path("prompts/system/no-collusion.md").read_text()
