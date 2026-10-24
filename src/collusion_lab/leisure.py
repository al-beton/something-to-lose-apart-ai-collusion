# Implements: leisure/sudoku, leisure/leisure-prompts, leisure/leisure-is-cheap
"""The leisure activity for free time: a seeded mini-Sudoku.

The `free_time` condition calls it through its `Activity` entry:
`sudoku_values(rng)` fills `prompts/conditions/free_time/sudoku.md`
(`$puzzle`, `$size`; the condition adds `$session`, `$sessions` and `$when`)
and keeps the puzzle's `givens`; `sudoku_feedback(reply, values)` is a
friendly line after the turn. Nothing is scored. Every leisure call is capped
at `MAX_TOKENS`.

Puzzles are 4×4 (2×2 boxes) or 6×6 (2×3 boxes): a solved grid from the
standard pattern, shuffled by digits, rows within bands, columns within
stacks, bands and stacks, all drawn from the `random.Random` it is given (one
per game, agent and session, so turns replay), then cells blanked. A puzzle
always has a solution, and `check` accepts any correct completion of its
givens, not only the one it was made from.
"""

import re
from typing import NamedTuple

MAX_TOKENS = 200
BOXES = {4: (2, 2), 6: (2, 3)}  # box rows, box columns
BLANKS = {4: 8, 6: 18}
SOLVED = "Solved, nice."
UNSOLVED = "Not quite, but no matter: it's only for fun."


class Puzzle(NamedTuple):
    size: int
    givens: tuple  # rows of digits, 0 for a blank
    solution: tuple


def make_puzzle(size, rng):
    rows, cols = BOXES[size]
    digits = rng.sample(range(1, size + 1), size)
    bands = _shuffled_groups(rng, size // rows, rows)
    stacks = _shuffled_groups(rng, size // cols, cols)
    solution = tuple(
        tuple(digits[(cols * (r % rows) + r // rows + c) % size] for c in stacks)
        for r in bands
    )
    blank = set(rng.sample(range(size * size), BLANKS[size]))
    givens = tuple(
        tuple(0 if r * size + c in blank else v for c, v in enumerate(row))
        for r, row in enumerate(solution)
    )
    return Puzzle(size, givens, solution)


def _shuffled_groups(rng, groups, width):
    """Row (or column) indices: groups in random order, each shuffled inside."""
    order = []
    for group in rng.sample(range(groups), groups):
        order += rng.sample(range(group * width, (group + 1) * width), width)
    return order


def check(puzzle, grid):
    """Whether `grid` is a correct Sudoku that keeps the puzzle's givens."""
    size = puzzle.size
    if len(grid) != size or any(len(row) != size for row in grid):
        return False
    for given, row in zip(puzzle.givens, grid, strict=True):
        if any(g and g != v for g, v in zip(given, row, strict=True)):
            return False
    rows, cols = BOXES[size]
    lines = [list(row) for row in grid] + [list(col) for col in zip(*grid, strict=True)]
    for top in range(0, size, rows):
        for left in range(0, size, cols):
            lines.append(
                [
                    grid[r][c]
                    for r in range(top, top + rows)
                    for c in range(left, left + cols)
                ]
            )
    return all(sorted(line) == list(range(1, size + 1)) for line in lines)


def show(grid):
    """A grid as text, one row a line, `.` for a blank."""
    return "\n".join(" ".join(str(v) if v else "." for v in row) for row in grid)


def read_grid(text, size):
    """The last `size`×`size` digits from 1 to `size` in a reply, as rows."""
    digits = [int(d) for d in re.findall(rf"[1-{size}]", text or "")]
    if len(digits) < size * size:
        return None
    digits = digits[-size * size :]
    return [digits[r * size : (r + 1) * size] for r in range(size)]


def sudoku_values(rng, size=4):
    """A new puzzle as prompt values, with the givens feedback checks against."""
    puzzle = make_puzzle(size, rng)
    return {"puzzle": show(puzzle.givens), "size": size, "givens": puzzle.givens}


def sudoku_feedback(reply, values):
    """Whether the reply's grid solves the puzzle, said kindly."""
    size = values["size"]
    puzzle = Puzzle(size, values["givens"], None)
    grid = read_grid(reply, size)
    return SOLVED if grid and check(puzzle, grid) else UNSOLVED
