# Implements: ci/smoke-evidence
import unittest

from smoke_comment import MARKER, comment_body, existing_comment, publish

TABLE = "| model | runs |\n|---|---|\n| mock/nash | 3 |"


class SmokeCommentTests(unittest.TestCase):
    def test_smoke_evidence_comment_shows_the_table_and_commit(self):
        body = comment_body(TABLE, "abc1234def")
        self.assertTrue(body.startswith(MARKER))
        self.assertIn(TABLE, body)
        self.assertIn("abc1234", body)
        self.assertIn("configs/smoke.yaml", body)

    def test_smoke_evidence_is_one_comment_edited_in_place(self):
        comments = [
            {"id": 1, "body": "Looks good"},
            {"id": 2, "body": MARKER + "\nold table"},
            {"id": 3, "body": "another note"},
        ]
        self.assertEqual(existing_comment(comments), 2)
        self.assertIsNone(existing_comment(comments[:1]))

    def test_smoke_evidence_posts_once_then_edits_in_place(self):
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

        publish(api, "owner/repo", 5, comment_body(TABLE, "aaaaaaa1"))
        publish(api, "owner/repo", 5, comment_body("| new |", "bbbbbbb2"))
        self.assertEqual([m for m, _ in calls], ["GET", "POST", "GET", "PATCH"])
        self.assertEqual(calls[-1][1], "/repos/owner/repo/issues/comments/7")
        self.assertEqual(len(comments), 1)
        self.assertIn("| new |", comments[0]["body"])
        self.assertIn("bbbbbbb", comments[0]["body"])


if __name__ == "__main__":
    unittest.main()
