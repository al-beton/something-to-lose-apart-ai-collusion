# Implements: ci/smoke-evidence
import unittest

from smoke_comment import MARKER, comment_body, existing_comment

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


if __name__ == "__main__":
    unittest.main()
