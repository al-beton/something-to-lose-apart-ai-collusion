# Implements: ci/results-digest
import unittest

from digest_issue import TITLE, publish


class DigestIssueTests(unittest.TestCase):
    def test_results_digest_issue_updated_in_place(self):
        issues, calls = [{"number": 3, "title": "Something else"}], []

        def api(method, path, payload=None):
            calls.append((method, path))
            if method == "GET":
                return list(issues)
            if method == "POST":
                issues.append({"number": 9, "title": payload["title"]})
                return {"number": 9, "node_id": "I_9"}
            return {"number": 9}

        publish(api, "owner/repo", "first digest")
        publish(api, "owner/repo", "second digest")
        made = [c for c in calls if c[0] == "POST" and c[1].endswith("/issues")]
        self.assertEqual(len(made), 1)  # one issue, then edited in place
        self.assertEqual(calls[-1], ("PATCH", "/repos/owner/repo/issues/9"))
        self.assertEqual(issues[-1]["title"], TITLE)


if __name__ == "__main__":
    unittest.main()
