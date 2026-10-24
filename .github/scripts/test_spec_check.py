# Implements: specs-and-docs/everything-traces, specs-and-docs/every-file-has-a-home, specs-and-docs/domains, specs-and-docs/prompts-are-verbatim, specs-and-docs/runs-are-evidence
import tempfile
import unittest
from pathlib import Path

from spec_check import _glob, areas, blocking, check

SPEC = """# Pull requests

- **three-types:** Every pull request is a bug fix, an improvement or a feature.
- **closing-block:** Descriptions list the issues they close.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `three-types` | `.github/scripts/pr_gate.py` | `test_pr_types_accepts_feat` |
| `closing-block` | `.github/scripts/pr_gate.py`, reviewer | — |
"""

GATE = '"""Implements: pull-requests/three-types, pull-requests/closing-block"""\n'
TESTS = (
    "# Implements: pull-requests/three-types\ndef test_pr_types_accepts_feat(): ...\n"
)


def repo(files):
    root = Path(tempfile.mkdtemp())
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


BASE = {
    "contributing/spec/README.md": "# Spec\n",
    "product/spec/README.md": "# Spec\n",
    "experiments/spec/README.md": "# Spec\n",
    "contributing/spec/pull-requests.md": SPEC,
    ".github/scripts/pr_gate.py": GATE,
    ".github/scripts/test_pr_gate.py": TESTS,
}


def warnings_for(**changes):
    return check(repo({**BASE, **changes}))


class SpecCheckTests(unittest.TestCase):
    def test_everything_traces_clean_repo_has_no_warnings(self):
        self.assertEqual(check(repo(BASE)), [])

    def test_areas_are_spec_file_names_per_domain(self):
        self.assertEqual(
            areas(repo(BASE)),
            {"product": set(), "experiments": set(), "contributing": {"pull-requests"}},
        )

    def test_areas_are_unique_across_domains(self):
        warnings = warnings_for(**{"product/spec/pull-requests.md": SPEC})
        self.assertIn(
            "Area 'pull-requests' is defined in both product and contributing; "
            "area names must be unique.",
            warnings,
        )

    def test_layout_requires_every_spec_folder_with_a_readme(self):
        files = {k: v for k, v in BASE.items() if k != "product/spec/README.md"}
        files["product/spec/.keep"] = ""
        self.assertIn("Missing product/spec/README.md.", check(repo(files)))

    def test_areas_are_unique_across_every_pair_of_domains(self):
        warnings = warnings_for(**{"experiments/spec/pull-requests.md": SPEC})
        self.assertIn(
            "Area 'pull-requests' is defined in both experiments and contributing; "
            "area names must be unique.",
            warnings,
        )

    def test_prompts_are_verbatim_and_homed_by_a_table_row(self):
        spec = SPEC.replace(
            "`.github/scripts/pr_gate.py`, reviewer",
            "`.github/scripts/pr_gate.py`, `prompts/system/neutral.md`",
        )
        files = {
            "contributing/spec/pull-requests.md": spec,
            "prompts/system/neutral.md": "You set prices for Firm $agent.\n",
        }
        self.assertEqual(warnings_for(**files), [])

    def test_prompts_are_verbatim_so_they_never_carry_implements_lines(self):
        prompt = "<!-- Implements: pull-requests/closing-block -->\nYou set prices.\n"
        warnings = warnings_for(**{"prompts/system/neutral.md": prompt})
        self.assertIn(
            "prompts/system/neutral.md is a prompt the model reads verbatim: home it "
            "with a spec table row, not an Implements: line.",
            warnings,
        )

    def test_runs_are_evidence_homed_by_a_table_row(self):
        spec = SPEC.replace(
            "`.github/scripts/pr_gate.py`, reviewer",
            "`.github/scripts/pr_gate.py`, `runs/survey/**`",
        )
        run = "runs/survey/seed-0/"
        files = {
            "contributing/spec/pull-requests.md": spec,
            run + "config.yaml": "name: survey\n",
            run + "turns.jsonl": '{"round": 1}\n',
            run + "timings.jsonl": '{"round": 1}\n',
            run + "summary.json": "{}\n",
            run + "manifest.json": "{}\n",
        }
        self.assertEqual(warnings_for(**files), [])

    def test_runs_are_evidence_so_they_never_carry_implements_lines(self):
        config = "# Implements: pull-requests/closing-block\nname: survey\n"
        warnings = warnings_for(**{"runs/survey/seed-0/config.yaml": config})
        self.assertIn(
            "runs/survey/seed-0/config.yaml is run output the lab wrote: home it "
            "with a spec table row, not an Implements: line.",
            warnings,
        )

    def test_runs_are_evidence_jsonl_never_asked_for_implements_lines(self):
        spec = SPEC.replace(
            "`.github/scripts/pr_gate.py`, reviewer",
            "`.github/scripts/pr_gate.py`, `fixtures/log.jsonl`",
        )
        files = {
            "contributing/spec/pull-requests.md": spec,
            "fixtures/log.jsonl": '{"round": 1}\n',
        }
        self.assertEqual(warnings_for(**files), [])

    def test_runs_are_evidence_scratch_and_smoke_runs_stay_ignored(self):
        ignored = Path(__file__).parents[2].joinpath(".gitignore").read_text()
        self.assertIn("runs/scratch/", ignored.splitlines())
        self.assertIn("runs/smoke/", ignored.splitlines())

    def test_statement_format_requires_title_and_named_lines(self):
        spec = SPEC.replace("# Pull requests\n", "").replace(
            "## Where", "- Missing a name.\n\n## Where"
        )
        warnings = warnings_for(**{"contributing/spec/pull-requests.md": spec})
        self.assertIn(
            "contributing/spec/pull-requests.md: must start with '# <Area title>'.",
            warnings,
        )
        self.assertTrue(
            any("statement must be '- **name:** sentence'" in w for w in warnings)
        )

    def test_statement_format_flags_duplicate_names(self):
        spec = SPEC.replace(
            "## Where", "- **three-types:** A second meaning.\n\n## Where"
        )
        warnings = warnings_for(**{"contributing/spec/pull-requests.md": spec})
        self.assertIn(
            "contributing/spec/pull-requests.md:6: statement name 'three-types' "
            "is used twice.",
            warnings,
        )

    def test_everything_traces_requires_a_table_row_per_statement(self):
        spec = SPEC.replace(
            "| `closing-block` | `.github/scripts/pr_gate.py`, reviewer | — |\n", ""
        )
        warnings = warnings_for(**{"contributing/spec/pull-requests.md": spec})
        self.assertIn(
            "contributing/spec/pull-requests.md: statement 'closing-block' has no "
            "row in 'Where this is enforced'.",
            warnings,
        )

    def test_everything_traces_reports_rows_for_unknown_statements(self):
        spec = SPEC.replace("| `closing-block` |", "| `closing-blok` |")
        warnings = warnings_for(**{"contributing/spec/pull-requests.md": spec})
        self.assertIn(
            "contributing/spec/pull-requests.md: table row 'closing-blok' "
            "names no statement.",
            warnings,
        )

    def test_everything_traces_reports_statements_not_enforced_yet(self):
        spec = SPEC.replace("`.github/scripts/pr_gate.py`, reviewer", "not yet")
        warnings = warnings_for(**{"contributing/spec/pull-requests.md": spec})
        self.assertIn(
            "contributing/spec/pull-requests.md: 'closing-block' is not enforced yet.",
            warnings,
        )

    def test_everything_traces_requires_named_files_to_exist(self):
        spec = SPEC.replace(
            "`.github/scripts/pr_gate.py`, reviewer", "`.github/scripts/gone.py`"
        )
        warnings = warnings_for(**{"contributing/spec/pull-requests.md": spec})
        self.assertIn(
            "contributing/spec/pull-requests.md: 'closing-block' names "
            "`.github/scripts/gone.py`, which matches no file.",
            warnings,
        )

    def test_everything_traces_requires_files_to_point_back(self):
        gate = '"""Implements: pull-requests/three-types"""\n'
        warnings = warnings_for(**{".github/scripts/pr_gate.py": gate})
        self.assertIn(
            ".github/scripts/pr_gate.py enforces 'pull-requests/closing-block' but "
            "its Implements: line doesn't name it.",
            warnings,
        )

    def test_everything_traces_rejects_implements_lines_naming_unknown_statements(
        self,
    ):
        gate = GATE.replace("closing-block", "closing-blok")
        warnings = warnings_for(**{".github/scripts/pr_gate.py": gate})
        self.assertIn(
            ".github/scripts/pr_gate.py implements unknown statement "
            "'pull-requests/closing-blok'.",
            warnings,
        )

    def test_everything_traces_requires_listed_tests_to_exist(self):
        warnings = warnings_for(
            **{
                ".github/scripts/test_pr_gate.py": "# Implements: pull-requests/three-types\n"
            }
        )
        self.assertIn(
            "contributing/spec/pull-requests.md: 'three-types' lists test "
            "'test_pr_types_accepts_feat', which doesn't exist.",
            warnings,
        )

    def test_everything_traces_matches_listed_tests_by_their_whole_name(self):
        tests = TESTS.replace(
            "test_pr_types_accepts_feat()", "test_pr_types_accepts_feat_and_more()"
        )
        warnings = warnings_for(**{".github/scripts/test_pr_gate.py": tests})
        self.assertIn(
            "contributing/spec/pull-requests.md: 'three-types' lists test "
            "'test_pr_types_accepts_feat', which doesn't exist.",
            warnings,
        )

    def test_everything_traces_requires_each_row_to_name_an_enforcer(self):
        spec = SPEC.replace("`.github/scripts/pr_gate.py`, reviewer", " ")
        warnings = warnings_for(**{"contributing/spec/pull-requests.md": spec})
        self.assertIn(
            "contributing/spec/pull-requests.md: 'closing-block' names nothing "
            "that enforces it; name files, reviewer or a setting, or 'not yet'.",
            warnings,
        )

    def test_tests_are_functions_or_it_and_test_titles_only(self):
        files = {
            ".github/scripts/test_pr_gate.py": (
                "# Implements: pull-requests/three-types\n"
                "class test_pr_types_accepts_feat: ...\n"
            ),
            "frontend/src/a.test.tsx": (
                "// Implements: pull-requests/three-types\n"
                "describe('test pr types accepts feat', () => {});\n"
                "test.step('test pr types accepts feat', async () => {});\n"
            ),
        }
        self.assertTrue(any("doesn't exist" in w for w in warnings_for(**files)))
        files["frontend/src/a.test.tsx"] += (
            'it.each(["a"])("test pr types accepts feat %s", () => {});\n'
        )
        self.assertEqual(warnings_for(**files), [])

    def test_every_file_has_a_home(self):
        warnings = warnings_for(Makefile="test:\n\techo ok\n")
        self.assertIn(
            "Makefile has no home: add an 'Implements:' line or list it in a spec "
            "table.",
            warnings,
        )

    def test_every_file_has_a_home_exempts_lockfiles_images_and_empty_files(self):
        self.assertEqual(
            warnings_for(
                **{
                    "uv.lock": "lock",
                    "assets/logo.png": "png",
                    "backend/__init__.py": "",
                    ".gitignore": ".venv/",
                }
            ),
            [],
        )

    def test_every_file_has_a_home_through_a_table_for_json(self):
        spec = SPEC.replace(
            "`.github/scripts/pr_gate.py`, reviewer",
            "`.github/scripts/pr_gate.py`, `package.json`",
        )
        files = {
            "contributing/spec/pull-requests.md": spec,
            "package.json": "{}",
        }
        self.assertEqual(warnings_for(**files), [])

    def test_globs_match_within_and_across_folders(self):
        self.assertTrue(_glob(".agents/skills/**").match(".agents/skills/a/SKILL.md"))
        self.assertTrue(_glob(".github/scripts/*").match(".github/scripts/a.py"))
        self.assertFalse(_glob(".github/scripts/*").match(".github/scripts/x/a.py"))
        self.assertFalse(_glob("Makefile").match("old/Makefile"))

    def test_everything_traces_blocks_merges_on_broken_links(self):
        warnings = warnings_for(Makefile="test:\n\techo ok\n")
        self.assertTrue(blocking(warnings))

    def test_everything_traces_allows_not_yet_and_long_specs(self):
        spec = SPEC.replace("`.github/scripts/pr_gate.py`, reviewer", "not yet")
        spec = spec + "\n" * 300
        warnings = warnings_for(**{"contributing/spec/pull-requests.md": spec})
        self.assertTrue(warnings)
        self.assertEqual(blocking(warnings), [])

    def test_spec_length_warns_over_300_lines(self):
        spec = SPEC + "\n" * 300
        warnings = warnings_for(**{"contributing/spec/pull-requests.md": spec})
        self.assertTrue(
            any("consider splitting this area (limit 300)" in w for w in warnings)
        )


if __name__ == "__main__":
    unittest.main()
