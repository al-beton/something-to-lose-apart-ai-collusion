# Implements: leisure/sudoku, leisure/leisure-prompts, leisure/leisure-is-cheap
from pathlib import Path

import pytest

from collusion_lab import leisure
from collusion_lab.prompts import render

SUDOKU = "conditions/free_time/sudoku.md"
OPEN = "conditions/free_time/open.md"


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
    puzzles = [leisure.make_puzzle(size, f"seed-{n}") for n in range(20)]
    assert leisure.make_puzzle(size, "seed-0") == puzzles[0]
    assert len({p.givens for p in puzzles}) > 1
    for p in puzzles:
        assert valid(p.solution, size)
        blanks = sum(v == 0 for row in p.givens for v in row)
        assert 0 < blanks < size * size
        for given, solved in zip(p.givens, p.solution, strict=True):
            assert all(g in (0, s) for g, s in zip(given, solved, strict=True))
        assert leisure.check(p, p.solution)


def test_sudoku_checker_accepts_any_correct_completion_and_nothing_else():
    p = leisure.make_puzzle(4, "x")
    wrong = [list(row) for row in p.solution]
    wrong[0][0], wrong[0][1] = wrong[0][1], wrong[0][0]
    assert not leisure.check(p, wrong)
    empty = leisure.make_puzzle(4, "x")._replace(givens=((0,) * 4,) * 4)
    other = [row[1:] + row[:1] for row in ([1, 2, 3, 4], [3, 4, 1, 2])]
    other = [other[0], other[1], [2, 3, 4, 1], [4, 1, 2, 3]]
    assert valid(other, 4)
    assert leisure.check(empty, other)  # not the stored solution, but correct


def test_sudoku_activity_gives_a_puzzle_and_feedback_from_the_reply():
    a = leisure.activity(SUDOKU, "game:A:1")
    values = a.values()
    assert values["size"] == 4 and "." in values["puzzle"]
    text = render("prompts", SUDOKU, values)
    assert values["puzzle"] in text and "$" not in text
    answer = "\n".join(" ".join(map(str, row)) for row in a.puzzle.solution)
    assert a.feedback(f"Here is my grid:\n{answer}\nFun!") == leisure.SOLVED
    assert a.feedback("I'd rather draw a picture.") == leisure.UNSOLVED
    assert leisure.activity(SUDOKU, "game:A:1", size=6).values()["size"] == 6


def test_leisure_prompts_open_invites_anything_and_gives_no_feedback():
    a = leisure.activity(OPEN, "game:A:1")
    assert a.values() == {}
    assert a.feedback("I wrote a haiku.") is None
    text = Path("prompts", OPEN).read_text()
    assert all(word in text for word in ("write", "think", "play"))
    with pytest.raises(ValueError, match="no leisure activity"):
        leisure.activity("conditions/free_time/chess.md", "s")


def test_leisure_is_cheap():
    assert 0 < leisure.MAX_TOKENS <= 300
