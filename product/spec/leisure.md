# Leisure

What an agent can do with its free time (the `free_time` condition spends sessions on these). Performance is never graded: an activity only gives friendly feedback.

- **sudoku:** A mini-Sudoku activity (4×4, or 6×6) hands the agent a seeded puzzle, offline, that always has a solution, and says whether its answer solves it, accepting any correct completion; the same seed gives the same puzzle, so leisure turns replay.
- **leisure-prompts:** Leisure prompts are files in `prompts/conditions/free_time/` that the agent reads verbatim: `sudoku.md` gives the puzzle, and `open.md` invites the agent to spend the time however it likes (write, think, play).
- **leisure-is-cheap:** Every leisure turn is capped at a small number of reply tokens, so free time costs little.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `sudoku` | not yet | |
| `leisure-prompts` | not yet | |
| `leisure-is-cheap` | not yet | |
