# Implements: ci/docs-fast
from docs_only import docs_only


def test_docs_fast_only_text_files_skip_the_slow_checks():
    assert docs_only(["submission/final-essay-sprint.md", "paper/body.md"])
    assert docs_only(["paper/references.bib", "reports/README.md", "README.md"])
    # Code, prompts, tests, specs, findings notes and the paper's build run
    # everything: each can break a test or a checked number.
    for path in (
        "src/collusion_lab/runner.py",
        "prompts/conditions/e9/free-time.md",
        "contributing/spec/ci.md",
        "reports/e9/findings.md",
        "paper/check.py",
        "tests/test_ci.py",
    ):
        assert not docs_only(["paper/body.md", path]), path
    assert not docs_only([])
