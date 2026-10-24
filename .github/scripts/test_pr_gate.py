# Implements: pull-requests/closing-block, pull-requests/three-types, pull-requests/title-shows-type-and-issues, specs-and-docs/areas
import unittest

from pr_gate import CLOSING_HELP, TITLE_HELP, problems

AREAS = {"pull-requests", "ci", "runs"}
TITLE = "improve(ci): check titles against the area registry (#9001)"
BODY = """## Issues
Closes #9001

## Spec changes
None
"""


def check(title=TITLE, body=BODY):
    return problems(title, body, AREAS)


class PrGateTests(unittest.TestCase):
    def test_title_format_accepts_a_valid_pull_request(self):
        self.assertEqual(check(), [])

    def test_pr_types_accept_feat_fix_and_improve_only(self):
        for kind in ("feat", "fix", "improve"):
            self.assertEqual(check(title=TITLE.replace("improve", kind)), [])
        self.assertIn(
            "Title type must be feat, fix or improve.",
            check(title=TITLE.replace("improve", "chore")),
        )

    def test_title_format_allows_several_issues(self):
        title = "feat(runs): run a game from one config (#9021, #9022)"
        body = "Closes #9021\nCloses #9022\n"
        self.assertEqual(check(title=title, body=body), [])

    def test_title_format_requires_an_area(self):
        self.assertIn(TITLE_HELP, check(title="fix: keep the seed (#9021)"))

    def test_title_format_rejects_missing_issue_and_free_text(self):
        self.assertIn(TITLE_HELP, check(title="improve(ci): check titles"))
        self.assertIn(TITLE_HELP, check(title="Sweep runner"))

    def test_title_area_must_exist_and_suggests_the_closest(self):
        title = TITLE.replace("(ci)", "(pull-request)")
        self.assertEqual(
            check(title=title),
            [
                (
                    "Unknown area 'pull-request'. Did you mean 'pull-requests'? Areas "
                    "are the spec files in product/spec, experiments/spec, "
                    "contributing/spec."
                )
            ],
        )

    def test_closing_block_requires_a_keyword_line(self):
        self.assertIn(CLOSING_HELP, check(body="This fixes the thing in #9001."))

    def test_closing_block_accepts_non_closing_words_and_lists(self):
        self.assertEqual(check(body="Part of #9001\n"), [])
        self.assertEqual(check(body="Fixes #9001, #9002\n"), [])

    def test_closing_block_ignores_html_comments(self):
        self.assertIn(CLOSING_HELP, check(body="<!-- Closes #9001 -->\n"))

    def test_title_issues_in_closing_block_must_all_be_listed(self):
        title = "feat(runs): run a game (#9011, #9012)"
        self.assertEqual(
            check(title=title, body="Closes #9011\n"),
            ["#9012 is in the title but not in the closing block."],
        )


if __name__ == "__main__":
    unittest.main()
