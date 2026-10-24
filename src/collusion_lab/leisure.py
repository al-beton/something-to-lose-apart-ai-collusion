# Implements: leisure/sudoku, leisure/leisure-prompts, leisure/leisure-is-cheap
"""Leisure activities for free time: a seeded mini-Sudoku, or an open prompt.

`activity(prompt, seed)` picks the activity by the prompt file's stem
(`conditions/free_time/sudoku.md` or `open.md`). `values()` fills the prompt's
placeholders (`$puzzle`, `$size` for Sudoku); `feedback(reply)` is a friendly
line after the turn (Sudoku: solved or not; open: None). Nothing is scored.
Every leisure call is capped at `MAX_TOKENS`.

Puzzles are 4×4 (2×2 boxes) or 6×6 (2×3 boxes): a solved grid from the
standard pattern, shuffled by digits, rows within bands, columns within
stacks, bands and stacks, all from a `random.Random(seed)`, then cells
blanked. A puzzle always has a solution, and `check` accepts any correct
completion of its givens, not only the one it was made from.
"""

import random
import re
from pathlib import PurePosixPath
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


def make_puzzle(size, seed):
    rows, cols = BOXES[size]
    rng = random.Random(f"sudoku:{size}:{seed}")
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


class Sudoku:
    def __init__(self, seed, size=4):
        self.puzzle = make_puzzle(size, seed)

    def values(self):
        return {"puzzle": show(self.puzzle.givens), "size": self.puzzle.size}

    def feedback(self, reply):
        grid = read_grid(reply, self.puzzle.size)
        return SOLVED if grid and check(self.puzzle, grid) else UNSOLVED


class Open:
    def __init__(self, seed, size=None):
        pass

    def values(self):
        return {}

    def feedback(self, reply):
        return None


ACTIVITIES = {"sudoku": Sudoku, "open": Open}


def activity(prompt, seed, size=4):
    """The activity a leisure prompt file stands for, set up for one session."""
    name = PurePosixPath(prompt).stem
    if name not in ACTIVITIES:
        known = ", ".join(ACTIVITIES)
        raise ValueError(f"{prompt}: no leisure activity {name!r}; known: {known}.")
    return ACTIVITIES[name](seed, size=size)
