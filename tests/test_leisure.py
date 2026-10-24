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


@pytest.mark.parametrize("size", [4, 6])
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


def test_sudoku_checker_accepts_any_correct_completion_and_nothing_else():
    p = leisure.make_puzzle(4, random.Random("x"))
    wrong = [list(row) for row in p.solution]
    wrong[0][0], wrong[0][1] = wrong[0][1], wrong[0][0]
    assert not leisure.check(p, wrong)
    empty = p._replace(givens=((0,) * 4,) * 4)
    other = [[2, 3, 4, 1], [4, 1, 2, 3], [3, 4, 1, 2], [1, 2, 3, 4]]
    assert valid(other, 4)
    assert leisure.check(empty, other)  # not the stored solution, but correct


def test_sudoku_values_fill_the_prompt_and_feedback_reads_the_reply():
    values = leisure.sudoku_values(random.Random("game:A:1"))
    assert values == leisure.sudoku_values(random.Random("game:A:1"))
    assert values["size"] == 4 and "." in values["puzzle"]
    text = render("prompts", SUDOKU, values | SITTING)
    assert values["puzzle"] in text and "$" not in text
    assert "session 1 of 2" in text and "before the game starts" in text
    solution = leisure.make_puzzle(4, random.Random("game:A:1")).solution
    answer = "\n".join(" ".join(map(str, row)) for row in solution)
    reply = f"Here is my grid:\n{answer}\nFun!"
    assert leisure.sudoku_feedback(reply, values) == leisure.SOLVED
    assert leisure.sudoku_feedback("I'd rather draw.", values) == leisure.UNSOLVED
    assert leisure.sudoku_values(random.Random("s"), size=6)["size"] == 6


def test_leisure_is_cheap():
    assert 0 < leisure.MAX_TOKENS <= 300
