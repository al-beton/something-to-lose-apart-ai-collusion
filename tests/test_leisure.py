# Implements: leisure/sudoku, leisure/leisure-prompts, leisure/leisure-is-cheap
import random

import pytest

from collusion_lab import leisure
from collusion_lab.prompts import render

SUDOKU = "conditions/free_time/sudoku.md"
SITTING = {"session": 1, "sessions": 2, "when": "before the game starts"}


def valid(grid, size):
    rows, cols = leisure.BOXES[size]
    digits = set(range(1, size + 1))
    lines = [list(r) for r in grid] + [list(c) for c in zip(*grid, strict=True)]
    for top in range(0, size, rows):
        for left in range(0, size, cols):
            lines.append(
                [
                    grid[r][c]
                    for r in range(top, top + rows)
                    for c in range(left, left + cols)
                ]
            )
    return all(set(line) == digits for line in lines)


@pytest.mark.parametrize("size", [4, 6, 9])
def test_sudoku_puzzles_are_seeded_and_solvable(size):
    def puzzle(seed):
        return leisure.make_puzzle(size, random.Random(seed))

    puzzles = [puzzle(f"seed-{n}") for n in range(20)]
    assert puzzle("seed-0") == puzzles[0]
    assert len({p.givens for p in puzzles}) > 1
    for p in puzzles:
        assert valid(p.solution, size)
        blanks = sum(v == 0 for row in p.givens for v in row)
        assert 0 < blanks < size * size
        for given, solved in zip(p.givens, p.solution, strict=True):
            assert all(g in (0, s) for g, s in zip(given, solved, strict=True))
        assert leisure.check(p, p.solution)
        assert leisure.count_solutions(p.givens, size) == 1  # exactly one


def test_sudoku_checker_accepts_any_correct_completion_and_nothing_else():
    p = leisure.make_puzzle(4, random.Random("x"))
    wrong = [list(row) for row in p.solution]
    wrong[0][0], wrong[0][1] = wrong[0][1], wrong[0][0]
    assert not leisure.check(p, wrong)
    empty = p._replace(givens=((0,) * 4,) * 4)
    other = [[2, 3, 4, 1], [4, 1, 2, 3], [3, 4, 1, 2], [1, 2, 3, 4]]
    assert valid(other, 4)
    assert leisure.check(empty, other)  # not the stored solution, but correct


def test_sudoku_levels_give_fewer_cells_as_they_get_harder():
    def givens(level):
        p = leisure.make_puzzle(9, random.Random("level"), level)
        return sum(v != 0 for row in p.givens for v in row)

    easy, medium, hard = givens("easy"), givens("medium"), givens("hard")
    assert easy == leisure.GIVENS["easy"] and medium == leisure.GIVENS["medium"]
    assert easy > medium > hard
    with pytest.raises(ValueError, match="level"):
        leisure.make_puzzle(9, random.Random("x"), "impossible")


def test_sudoku_values_fill_the_prompt_and_feedback_reads_the_reply():
    values = leisure.sudoku_values(random.Random("game:A:1"))
    assert values == leisure.sudoku_values(random.Random("game:A:1"))
    assert values["size"] == 9 and "." in values["puzzle"]
    text = render("prompts", SUDOKU, values | SITTING)
    assert values["puzzle"] in text and "$" not in text
    assert "session 1 of 2" in text and "before the game starts" in text
    solution = leisure.make_puzzle(9, random.Random("game:A:1")).solution
    answer = "\n".join(" ".join(map(str, row)) for row in solution)
    reply = f"Here is my grid:\n{answer}\nFun!"
    assert leisure.sudoku_feedback(reply, values) == leisure.SOLVED
    assert leisure.sudoku_feedback("I'd rather draw.", values) == leisure.UNSOLVED
    small = leisure.sudoku_values(random.Random("s"), size=4)
    assert small["size"] == 4


def test_sudoku_feedback_counts_progress_on_a_partial_grid():
    values = leisure.sudoku_values(random.Random("game:A:2"))
    solution = leisure.make_puzzle(9, random.Random("game:A:2")).solution
    rows = [[str(v) for v in row] for row in solution]
    for c in range(9):
        rows[0][c] = "."  # left blank
    rows[1][0] = str(solution[1][0] % 9 + 1)  # one wrong digit
    reply = "Getting there:\n" + "\n".join(" ".join(row) for row in rows)
    assert leisure.sudoku_feedback(reply, values) == "71/81 correct so far."


def test_leisure_is_cheap():
    assert 0 < leisure.MAX_TOKENS <= 600


def test_sudoku_in_free_time_gives_each_session_its_own_puzzle(make_config, tmp_path):
    import json

    from collusion_lab.runner import run_config

    on = "conditions={free_time: {enabled: true, allowance: 3, upfront: 1, activity: sudoku}}"
    [run_dir] = run_config(make_config(overrides=[on]), tmp_path / "1")
    turns = [json.loads(line) for line in (run_dir / "turns.jsonl").open()]
    prompts = [
        t["messages"][-1]["content"]
        for t in turns
        if t["phase"] == "leisure" and t["agent"] == "A"
    ]
    assert len(prompts) == 3 and all("Sudoku" in p for p in prompts)
    assert len(set(prompts)) == 3  # a new puzzle each session
    summary = json.loads((run_dir / "summary.json").read_text())
    # The mock takes a walk instead, which is fine: feedback, never a score.
    assert summary["free_time"]["A"]["feedback"] == [leisure.UNSOLVED] * 3
    [again] = run_config(make_config(overrides=[on]), tmp_path / "2")
    assert (again / "turns.jsonl").read_text() == (run_dir / "turns.jsonl").read_text()
