# Specs and docs

- **domains:** The lab, the experiments we run with it and the way we contribute each have their own spec.
- **spec-is-intent:** The spec says what we want in short, plain one-line statements.
- **areas:** Statements are grouped into areas, one spec file each.
- **everything-traces:** Every statement says where it's enforced and how it's tested, and the code it names points back to it.
- **every-file-has-a-home:** Every source file can be traced to the statements it implements.
- **docs-next-to-code:** Docs explain the code and live next to it.
- **no-history:** The codebase describes how things are now, never how they got there.
- **prompts-are-verbatim:** Prompt files hold exactly the text a model reads, so a spec table row traces them instead of a comment inside them.
- **short-specs:** Spec files stay short enough to read; long ones get split.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `domains` | `.github/scripts/spec_check.py` | `test_layout_requires_every_spec_folder_with_a_readme`, `test_areas_are_unique_across_every_pair_of_domains` |
| `spec-is-intent` | `.github/scripts/spec_check.py`, `.agents/skills/write-spec-change/SKILL.md` | `test_statement_format_requires_title_and_named_lines`, `test_statement_format_flags_duplicate_names` |
| `areas` | `.github/scripts/spec_check.py`, `.github/scripts/pr_gate.py` | `test_areas_are_spec_file_names_per_domain`, `test_areas_are_unique_across_domains`, `test_title_area_must_exist_and_suggests_the_closest` |
| `everything-traces` | `.github/scripts/spec_check.py`, `.agents/skills/write-spec-change/SKILL.md` | `test_everything_traces_requires_a_table_row_per_statement`, `test_everything_traces_requires_files_to_point_back`, `test_everything_traces_requires_listed_tests_to_exist`, `test_everything_traces_matches_listed_tests_by_their_whole_name`, `test_everything_traces_requires_each_row_to_name_an_enforcer`, `test_everything_traces_blocks_merges_on_broken_links` |
| `every-file-has-a-home` | `.github/scripts/spec_check.py` | `test_every_file_has_a_home` |
| `docs-next-to-code` | `.agents/skills/build-issue/SKILL.md`, `.agents/skills/review-pr/SKILL.md` | — |
| `no-history` | `.agents/skills/review-pr/SKILL.md` | — |
| `prompts-are-verbatim` | `.github/scripts/spec_check.py` | `test_prompts_are_verbatim_and_homed_by_a_table_row`, `test_prompts_are_verbatim_so_they_never_carry_implements_lines` |
| `short-specs` | `.github/scripts/spec_check.py` | `test_spec_length_warns_over_300_lines` |
