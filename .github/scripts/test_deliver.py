# Implements: commits/named-paths, review/review-finished, merging/stacked-retarget, merging/main-stays-green, merging/merge-when-clean
import json
import unittest

from deliver import (
    MergeRefused,
    closing_lines,
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

    def __init__(self, checks="pass", unresolved=0, stacked=(21,)):
        self.calls = []
        self.checks = checks
        self.unresolved = unresolved
        self.stacked = stacked

    def __call__(self, *args):
        self.calls.append(args)
        if args[:2] == ("pr", "view"):
            return json.dumps(
                {
                    "number": 20,
                    "title": "improve(workflow): one routine (#18)",
                    "body": "## Issues\nCloses #18\n\n## Notes\nNone",
                    "headRefName": "18-deliver-issue",
                    "baseRefName": "main",
                    "headRefOid": "abc",
                }
            )
        if args[:2] == ("pr", "checks"):
            return f"blocking-checks\t{self.checks}\t3s\turl\n"
        if args[:2] == ("pr", "list"):
            return json.dumps([{"number": n} for n in self.stacked])
        if args[:2] == ("repo", "view"):
            return json.dumps({"owner": {"login": "o"}, "name": "r"})
        if args[:2] == ("api", "graphql"):
            threads = [{"isResolved": False}] * self.unresolved
            threads += [{"isResolved": True}]
            pr = {"reviewThreads": {"nodes": threads}}
            return json.dumps({"data": {"repository": {"pullRequest": pr}}})
        if args[:2] == ("run", "list"):
            return json.dumps([{"databaseId": 7}])
        return ""

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

    def test_merge_when_clean_keeps_the_closing_block(self):
        body = "## Issues\nCloses #18\nRefs #3\n\nCloses nothing here"
        self.assertEqual(closing_lines(body), ["Closes #18", "Refs #3"])

    def test_stacked_retarget_happens_before_the_branch_is_deleted(self):
        gh = FakeGh()
        merge(20, gh)
        retarget = gh.index("pr", "edit", "21", "--base", "main")
        squash = gh.index("pr", "merge", "20", "--squash")
        delete = gh.index("git", "push", "origin", "--delete", "18-deliver-issue")
        self.assertLess(retarget, squash)
        self.assertLess(squash, delete)
        merged = gh.calls[squash]
        self.assertNotIn("--delete-branch", merged)
        self.assertIn("improve(workflow): one routine (#18)", merged)
        self.assertIn("Closes #18", merged[merged.index("--body") + 1])

    def test_main_stays_green_reruns_checks_after_merging(self):
        gh = FakeGh(stacked=())
        merge(20, gh)
        dispatch = gh.index("workflow", "run", "blocking-checks.yml", "--ref", "main")
        watch = gh.index("run", "watch", "7")
        self.assertLess(gh.index("pr", "merge"), dispatch)
        self.assertLess(dispatch, watch)
        self.assertIn("--exit-status", gh.calls[watch])

    def test_merge_when_clean_refuses_red_checks_or_open_threads(self):
        for gh in (FakeGh(checks="fail"), FakeGh(unresolved=1)):
            with self.assertRaises(MergeRefused):
                merge(20, gh)
            self.assertFalse([c for c in gh.calls if c[:2] == ("pr", "merge")])


if __name__ == "__main__":
    unittest.main()
