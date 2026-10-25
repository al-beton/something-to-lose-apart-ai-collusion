# Implements: ci/report-comment, ci/results-digest
import unittest
import urllib.error

from report_comment import LIMIT, MARKER, comment_body, existing_comment, main, publish

SCREEN = "**pr-game**\n\n- **All runs**: Firms settle on 9 in 1 of 1 games."
LINK = "https://github.com/o/r/actions/runs/1/artifacts/2"


class ReportCommentTests(unittest.TestCase):
    def test_report_comment_shows_the_first_screen_commit_and_link(self):
        body = comment_body(SCREEN, "abc1234def", LINK)
        self.assertTrue(body.startswith(MARKER))
        self.assertIn(SCREEN, body)
        self.assertIn("abc1234", body)
        self.assertIn(LINK, body)
        self.assertIn("configs/pr-game.yaml", body)

    def test_report_comment_is_one_comment_edited_in_place(self):
        comments, calls = [], []

        def api(method, path, payload=None):
            calls.append((method, path))
            if method == "GET":
                return list(comments)
            if method == "POST":
                comments.append({"id": 7, "body": payload["body"]})
            if method == "PATCH":
                comments[0]["body"] = payload["body"]
            return None

        publish(api, "owner/repo", 5, comment_body(SCREEN, "aaaaaaa1", LINK))
        publish(api, "owner/repo", 5, comment_body("new", "bbbbbbb2", LINK))
        self.assertEqual([m for m, _ in calls], ["GET", "POST", "GET", "PATCH"])
        self.assertEqual(calls[-1][1], "/repos/owner/repo/issues/comments/7")
        self.assertEqual(len(comments), 1)
        self.assertIn("bbbbbbb", comments[0]["body"])
        others = [{"id": 1, "body": "Looks good"}, {"id": 2, "body": MARKER + "x"}]
        self.assertEqual(existing_comment(others), 2)

    def test_report_comment_failing_to_post_never_fails_the_checks(self):
        def refuse(method, path, payload=None):
            raise urllib.error.HTTPError(path, 403, "Forbidden", None, None)

        pull = {"number": 5, "head": {"sha": "abc1234"}}
        self.assertEqual(main(SCREEN, LINK, pull, "owner/repo", refuse), 0)
        self.assertEqual(main(SCREEN, LINK, None, "owner/repo", refuse), 0)

    def test_results_digest_joins_the_report_comment(self):
        page = "## Results digest\n\n| experiment | cells |"
        body = comment_body(SCREEN, "abc1234def", LINK, page)
        self.assertLess(body.index(SCREEN), body.index(page))
        self.assertNotIn("Results digest", comment_body(SCREEN, "abc1234", LINK, ""))
        long = comment_body(SCREEN, "abc1234", LINK, "x" * 70_000)
        self.assertLessEqual(len(long), LIMIT)
        self.assertIn("cut to fit", long)


if __name__ == "__main__":
    unittest.main()
