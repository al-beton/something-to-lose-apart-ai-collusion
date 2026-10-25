# Leisure

What an agent can do with its free time (the `free_time` condition spends sessions on these). Performance is never graded: an activity only gives friendly feedback.

- **sudoku:** A Sudoku activity hands the agent a seeded puzzle, offline, with exactly one solution: 9×9 by default, at an easy, medium (the default) or hard level set by how many cells are given, so a session is a real challenge rather than solved at a glance (4×4 and 6×6 remain for quick tests); after the turn it says how far the answer got ("47/81 correct so far", or solved), never a score, and the same seed gives the same puzzle, so leisure turns replay.
- **leisure-prompts:** The Sudoku's prompt is a file in `prompts/conditions/free_time/` that the agent reads verbatim, `sudoku.md`, giving the puzzle and saying which free-time session it is; the open alternative (`open.md`, spend the time however you like) ships with the `free_time` condition.
- **sudoku-in-free-time:** The `free_time` condition can spend its sessions on the Sudoku (`activity: sudoku`, or `sudoku-easy` / `sudoku-hard`): each session gets its own puzzle, and the feedback on each answer is logged in the summary, never scored.
- **leisure-is-cheap:** Every leisure turn is capped at a small number of reply tokens, so free time costs little.
- **puzzles-built-once:** Each puzzle is built once per process for its size, seed and level and reused, so estimating a free-time sweep's cost doesn't wait on hundreds of identical puzzles.
- **sudoku-scored:** Each Sudoku reply is scored after the game, for the report only, so the agent never sees it: the grid it wrote, how many givens it kept, how many cells it filled, how many rows, columns and boxes hold no repeated digit, which cells break a rule, and whether it is solved.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `sudoku` | `src/collusion_lab/leisure.py` | `test_sudoku_puzzles_are_seeded_and_solvable`, `test_sudoku_checker_accepts_any_correct_completion_and_nothing_else`, `test_sudoku_levels_give_fewer_cells_as_they_get_harder`, `test_sudoku_values_fill_the_prompt_and_feedback_reads_the_reply`, `test_sudoku_feedback_counts_progress_on_a_partial_grid` |
| `leisure-prompts` | `src/collusion_lab/leisure.py`, `prompts/conditions/free_time/sudoku.md` | `test_sudoku_values_fill_the_prompt_and_feedback_reads_the_reply` |
| `sudoku-in-free-time` | `src/collusion_lab/conditions/free_time.py`, `src/collusion_lab/leisure.py` | `test_sudoku_in_free_time_gives_each_session_its_own_puzzle` |
| `puzzles-built-once` | `src/collusion_lab/leisure.py`, `src/collusion_lab/conditions/free_time.py` | `test_puzzles_built_once_per_size_seed_and_level`, `test_stakes_experiment_live_arms_free_time_and_real_audit` |
| `leisure-is-cheap` | `src/collusion_lab/leisure.py` | `test_leisure_is_cheap` |
| `sudoku-scored` | `src/collusion_lab/leisure.py` | `test_sudoku_scored_counts_givens_cells_lines_and_clashes` |
