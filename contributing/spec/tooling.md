# Tooling

- **one-command-each:** Installing, linting, testing and checking the spec are each one command.
- **locked-dependencies:** Dependencies are locked, so every machine installs the same versions.
- **quick-start:** The README takes a newcomer from a fresh clone to a free mock run, its report and then a real model run in minutes, without asking anyone.
- **key-setup:** The README says where to get a model API key, how to cap its spending and that the sprint gives no model credits, and an example env file shows which variable to fill in.
- **how-tos:** The README says where to make each common change (a prompt, a model, a sweep, the market, a highlight rule, an experiment), naming the file and the spec area, and every file it names exists.
- **how-we-work:** The README gives people the working process in five lines and sends coding agents to `AGENTS.md`.
- **open-license:** The repository is public under the MIT license, so anyone can reuse the lab.
- **fast-tests:** Tests that only read a played game share one play of it per test module, and a test that changes a played game works on its own copy, so the whole suite stays quick to run.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-command-each` | `Makefile`, `README.md`, `pyproject.toml` | — |
| `locked-dependencies` | `uv.lock`, `.python-version`, `Makefile` | — |
| `quick-start` | `README.md` | `test_quick_start_goes_from_clone_to_a_report_then_a_real_run` |
| `key-setup` | `README.md`, `.env.example` | `test_key_setup_names_the_variable_spend_limit_and_no_sprint_credits` |
| `how-tos` | `README.md` | `test_how_tos_name_files_and_spec_areas_that_exist` |
| `how-we-work` | `README.md` | `test_how_we_work_is_five_lines_and_points_agents_to_agents_md` |
| `open-license` | `LICENSE` | — |
| `fast-tests` | `tests/conftest.py`, `tests/test_reports.py`, `tests/test_sweeps.py`, `tests/test_paper.py` | — |
