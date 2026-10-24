# Implements: commits/named-paths, review/review-finished, merging/stacked-retarget, merging/main-stays-green, merging/merge-when-clean
import json
import unittest

from deliver import (
    MergeRefused,
    closing_lines,
    commit,
    merge,
    review_finished,
    review_state,
    unsafe_paths,
)


def summary(sha, status):
    state = {"code_review": {"commit_sha": sha, "status": status}}
    return {"body": f"<!-- codex-review-state:v1 {json.dumps(state)} -->\n## Codex"}


class FakeGh:
    """Answers the commands `merge` runs; records every one."""

    def __init__(self, checks="pass", unresolved=0, stacked=(102,)):
        self.calls = []
        self.checks = checks
        self.unresolved = unresolved
        self.stacked = stacked

    def __call__(self, *args):
        self.calls.append(args)
        threads = [{"isResolved": False}] * self.unresolved + [{"isResolved": True}]
        pr = {"reviewThreads": {"nodes": threads}}
        answers = {
            ("pr", "view"): {
                "number": 101,
                "title": "improve(workflow): one routine (#7)",
                "body": "## Issues\nCloses #7\n\n## Notes\nNone",
                "headRefName": "7-one-routine",
                "baseRefName": "main",
                "headRefOid": "abc",
            },
            ("pr", "list"): [{"number": n} for n in self.stacked],
            ("repo", "view"): {"owner": {"login": "o"}, "name": "r"},
            ("api", "graphql"): {"data": {"repository": {"pullRequest": pr}}},
            ("run", "list"): [{"databaseId": 7}],
        }
        if args[:2] == ("pr", "checks"):
            return f"blocking-checks\t{self.checks}\t3s\turl\n"
        return json.dumps(answers[args[:2]]) if args[:2] in answers else ""

    def index(self, *prefix):
        return next(i for i, c in enumerate(self.calls) if c[: len(prefix)] == prefix)


class DeliverTests(unittest.TestCase):
    def test_review_finished_reads_the_state_marker_not_the_first_comment(self):
        comments = [{"body": "@codex review"}, summary("abc", "running")]
        self.assertFalse(review_finished(review_state(comments), "abc"))
        comments[1] = summary("abc", "completed")
        self.assertTrue(review_finished(review_state(comments), "abc"))
        self.assertIsNone(review_state([{"body": "Looks good"}]))

    def test_review_finished_only_on_the_latest_commit(self):
        state = review_state([summary("old", "completed")])
        self.assertFalse(review_finished(state, "new"))

    def test_named_paths_refuse_everything_and_run_output(self):
        self.assertEqual(
            unsafe_paths([".", "-A", "src/x.py", "runs/scratch/a", "./runs"]),
            [".", "-A", "runs/scratch/a", "./runs"],
        )
        self.assertEqual(unsafe_paths(["runs/x"], allow_runs=True), [])
        self.assertEqual(unsafe_paths(["src", "tests/test_x.py"]), [])

    def test_named_paths_commit_only_what_they_name(self):
        calls = []
        commit(["a.py", "b.md"], ["Subject", "Body"], run=lambda *a: calls.append(a))
        self.assertEqual(calls[0], ("git", "add", "--", "a.py", "b.md"))
        made = calls[1]
        self.assertEqual(made[:2], ("git", "commit"))
        self.assertIn("--only", made)
        self.assertEqual(made[made.index("--") :], ("--", "a.py", "b.md"))

    def test_merge_when_clean_keeps_the_closing_block(self):
        body = "## Issues\nCloses #7\nRefs #3\n\nCloses nothing here"
        self.assertEqual(closing_lines(body), ["Closes #7", "Refs #3"])

    def test_stacked_retarget_happens_before_the_branch_is_deleted(self):
        gh = FakeGh()
        merge(101, gh, pause=lambda seconds: None)
        retarget = gh.index("pr", "edit", "102", "--base", "main")
        squash = gh.index("pr", "merge", "101", "--squash")
        delete = gh.index("git", "push", "origin", "--delete", "7-one-routine")
        self.assertLess(retarget, squash)
        self.assertLess(squash, delete)
        merged = gh.calls[squash]
        self.assertNotIn("--delete-branch", merged)
        self.assertIn("improve(workflow): one routine (#7)", merged)
        self.assertIn("Closes #7", merged[merged.index("--body") + 1])

    def test_main_stays_green_reruns_checks_after_merging(self):
        gh = FakeGh(stacked=())
        merge(101, gh, pause=lambda seconds: None)
        dispatch = gh.index("workflow", "run", "blocking-checks.yml", "--ref", "main")
        watch = gh.index("run", "watch", "7")
        self.assertLess(gh.index("pr", "merge"), dispatch)
        self.assertLess(dispatch, watch)
        self.assertIn("--exit-status", gh.calls[watch])

    def test_merge_when_clean_refuses_red_checks_or_open_threads(self):
        for gh in (FakeGh(checks="fail"), FakeGh(unresolved=1)):
            with self.assertRaises(MergeRefused):
                merge(101, gh, pause=lambda seconds: None)
            self.assertFalse([c for c in gh.calls if c[:2] == ("pr", "merge")])


if __name__ == "__main__":
    unittest.main()
