# Pull requests

- **three-types:** Every pull request is a bug fix, an improvement or a new feature.
- **title-shows-type-and-issues:** Pull request titles follow a strict standard that shows the type, the area and the linked issues.
- **template:** Pull request descriptions follow the template: issues, spec changes, how it's built, tests, notes.
- **closing-block:** Pull request descriptions list every issue they close or contribute to, using GitHub's closing keywords.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `three-types` | `.github/scripts/pr_gate.py` | `test_pr_types_accept_feat_fix_and_improve_only` |
| `title-shows-type-and-issues` | `.github/scripts/pr_gate.py`, `.agents/skills/open-pr/SKILL.md` | `test_title_format_accepts_a_valid_pull_request`, `test_title_format_requires_an_area`, `test_title_area_must_exist_and_suggests_the_closest` |
| `template` | `.github/pull_request_template.md`, `.agents/skills/open-pr/SKILL.md` | — |
| `closing-block` | `.github/scripts/pr_gate.py`, `.agents/skills/open-pr/SKILL.md` | `test_closing_block_requires_a_keyword_line`, `test_title_issues_in_closing_block_must_all_be_listed` |
