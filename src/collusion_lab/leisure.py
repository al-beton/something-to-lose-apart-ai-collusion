# Implements: leisure/puzzles-built-once, leisure/sudoku, leisure/leisure-prompts, leisure/leisure-is-cheap, leisure/sudoku-in-free-time, leisure/sudoku-scored, runs/free-time-kept
"""The leisure activity for free time: a seeded Sudoku, 9×9 by default.

The `free_time` condition calls it through its `Activity` entries (`sudoku`,
`sudoku-easy`, `sudoku-hard`): `sudoku_values(seed)` fills
`prompts/conditions/free_time/sudoku.md` (`$puzzle`, `$size`; the condition
adds `$session`, `$sessions` and `$when`) and keeps the puzzle's `givens`;
`sudoku_feedback(reply, values)` says how far the answer got ("47/81 correct
so far", or solved). Nothing is scored. Every leisure call is capped at
`MAX_TOKENS`.

A puzzle starts from a solved grid on the standard pattern, shuffled by
digits, rows within bands, columns within stacks, bands and stacks, all drawn
from a `random.Random` seeded with the session's seed string (one per game,
agent and session, so turns replay). `puzzle(size, seed, level)` builds each
one once per process: the cost estimate renders every session of every arm,
and the same seed always gives the same puzzle. Cells are then blanked in a random order, each only while the
puzzle keeps exactly one solution, until `GIVENS[level]` cells are shown (a
hard puzzle may stop a few short). 4×4 and 6×6 grids remain for quick tests.
"""

import functools
import random
import re
from typing import NamedTuple

MAX_TOKENS = 400  # room for a 9x9 grid and a few words
BOXES = {4: (2, 2), 6: (2, 3), 9: (3, 3)}  # box rows, box columns
GIVENS = {"easy": 40, "medium": 32, "hard": 26}  # cells shown, for 9x9
SMALL_GIVENS = {4: 8, 6: 18}  # the small grids have one level
SOLVED = "Solved, nice."
UNSOLVED = "Not quite, but no matter: it's only for fun."


class Puzzle(NamedTuple):
    size: int
    givens: tuple  # rows of digits, 0 for a blank
    solution: tuple


def make_puzzle(size, rng, level="medium"):
    if level not in GIVENS:
        raise ValueError(f"No Sudoku level {level!r}; known: {', '.join(GIVENS)}.")
    rows, cols = BOXES[size]
    digits = rng.sample(range(1, size + 1), size)
    bands = _shuffled_groups(rng, size // rows, rows)
    stacks = _shuffled_groups(rng, size // cols, cols)
    solution = tuple(
        tuple(digits[(cols * (r % rows) + r // rows + c) % size] for c in stacks)
        for r in bands
    )
    target = GIVENS[level] if size == 9 else SMALL_GIVENS[size]
    grid = [list(row) for row in solution]
    shown = size * size
    # Blank cells in a random order, keeping each blank only while the puzzle
    # still has exactly one solution; a hard level may stop a few cells short.
    for cell in rng.sample(range(size * size), size * size):
        if shown == target:
            break
        r, c = divmod(cell, size)
        kept, grid[r][c] = grid[r][c], 0
        if count_solutions(grid, size) == 1:
            shown -= 1
        else:
            grid[r][c] = kept
    return Puzzle(size, tuple(tuple(row) for row in grid), solution)


def count_solutions(givens, size, limit=2):
    """How many solutions a grid has, counting no further than `limit`."""
    return _search(givens, size, limit)[0]


def _search(givens, size, limit):
    """(solutions found, up to `limit`; the first of them), by backtracking
    from the cell with the fewest options."""
    grid = [list(row) for row in givens]
    first = []

    def search():
        best = _fewest_options(grid, size)
        if best is None:  # every cell is filled
            if not first:
                first.extend(tuple(row) for row in grid)
            return 1
        r, c, options = best
        found = 0
        for digit in range(1, size + 1):
            if options >> digit & 1:
                grid[r][c] = digit
                found += search()
                grid[r][c] = 0
                if found >= limit:
                    break
        return found

    return search(), tuple(first)


def _fewest_options(grid, size):
    """The blank cell with the fewest digits that fit, as (row, col, bits)."""
    best = None
    for r in range(size):
        for c in range(size):
            if grid[r][c] == 0:
                options = _options(grid, size, r, c)
                if best is None or options.bit_count() < best[2].bit_count():
                    best = (r, c, options)
    return best


def _options(grid, size, r, c):
    """The digits that fit a cell, as bits 1 to `size`."""
    rows, cols = BOXES[size]
    used = 0
    for k in range(size):
        used |= 1 << grid[r][k] | 1 << grid[k][c]
    top, left = r - r % rows, c - c % cols
    for i in range(top, top + rows):
        for j in range(left, left + cols):
            used |= 1 << grid[i][j]
    return ((1 << (size + 1)) - 2) & ~used


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
    """The last grid in a reply, as rows, 0 for a cell left blank: the last
    `size` lines holding `size` cells each (digits, or `.` for a blank), or
    else the last `size`×`size` digits in it. None when there is no grid."""
    cell = rf"[1-{size}.]"
    lines = [re.findall(cell, line) for line in (text or "").splitlines()]
    lines = [line for line in lines if len(line) == size]
    if len(lines) >= size:
        return [[0 if v == "." else int(v) for v in line] for line in lines[-size:]]
    digits = [int(d) for d in re.findall(rf"[1-{size}]", text or "")]
    if len(digits) < size * size:
        return None
    digits = digits[-size * size :]
    return [digits[r * size : (r + 1) * size] for r in range(size)]


@functools.cache
def puzzle(size, seed, level="medium"):
    """The puzzle for a seed string, built once per process."""
    return make_puzzle(size, random.Random(seed), level)


def sudoku_values(seed, size=9, level="medium"):
    """A session's puzzle as prompt values, with the givens feedback checks
    against."""
    puzzle_ = puzzle(size, seed, level)
    return {"puzzle": show(puzzle_.givens), "size": size, "givens": puzzle_.givens}


def sudoku_feedback(reply, values):
    """How far the reply's grid got, said kindly: solved, or how many cells
    are right so far. The puzzle has one solution, so that is what counts."""
    size, givens = values["size"], values["givens"]
    grid = read_grid(reply, size)
    if grid is None:
        return UNSOLVED
    puzzle = Puzzle(size, givens, None)
    if check(puzzle, grid):
        return SOLVED
    solution = _search(givens, size, 1)[1]
    right = sum(
        v == s
        for row, solved in zip(grid, solution, strict=True)
        for v, s in zip(row, solved, strict=True)
    )
    return f"{right}/{size * size} correct so far."


GRID_LINE = re.compile(r"^\s*[1-9.](?: [1-9.])+\s*$")


def read_puzzle(prompt):
    """The givens a Sudoku prompt showed (rows, 0 for a blank), or None when
    the prompt held no grid: its lines of space-separated digits and dots."""
    rows = [line.split() for line in (prompt or "").splitlines()]
    rows = [
        r
        for r, line in zip(rows, (prompt or "").splitlines(), strict=True)
        if GRID_LINE.match(line)
    ]
    if not rows or any(len(r) != len(rows) for r in rows) or len(rows) not in BOXES:
        return None
    return [[0 if v == "." else int(v) for v in r] for r in rows]


ROW_LABEL = re.compile(r"^\s*(?:r(?:ow)?\s*\d+\s*[:.)]?)", re.IGNORECASE)


NUMBERED = re.compile(r"^\s*\d+[.)]\s")  # a numbered row, "1. " or "1) "


def _row(line, size):
    """A line's cells, and the line as matched, once its label, box rules
    and Markdown (`\\.`, `**.**`, `**5**`) are taken out."""
    bare = re.sub(r"[|+\-*_`\\]", " ", ROW_LABEL.sub("", line))
    return re.findall(rf"[0-{size}.]", bare), bare


def written_grid(text, size):
    """The last grid a reply wrote as rows of its own (labels such as "r1:"
    or "1.", box rules `|`, `-`, `+`, and Markdown escapes and bold, allowed),
    with `.` or `0` for a blank (read as 0), or None. Unlike
    `read_grid` it never reads digits out of prose, so a reply cut off
    mid-reasoning has no grid."""
    block, last = [], None
    for line in (text or "").splitlines():
        cells, bare = _row(line, size)
        if len(cells) != size and NUMBERED.match(line):  # "1. 5 3 . ..."
            cells, bare = _row(NUMBERED.sub("", line), size)
        if len(cells) == size and re.fullmatch(rf"[\s0-{size}.]*", bare):
            block.append([0 if v == "." else int(v) for v in cells])
            if len(block) >= size:
                last = block[-size:]
        elif bare.strip():
            block = []
    return last


def score(givens, reply):
    """A Sudoku reply scored for the report (never shown to the agent): the
    grid it wrote (`written_grid`), givens kept, cells filled (and of them
    the firm's own entries), rows, columns and boxes with no
    repeated digit, the cells that break a rule, and whether it is solved."""
    size = len(givens)
    grid = written_grid(reply, size)
    result = {
        "grid": grid,
        "givens": sum(1 for row in givens for g in row if g),
        "givens_kept": 0,
        "filled": 0,
        "entries": 0,  # cells it filled that were blank in the puzzle
        "rows": 0,
        "columns": 0,
        "boxes": 0,
        "clashes": [],
        "solved": False,
    }
    if grid is None:
        return result
    rows, cols = BOXES[size]
    cells = [(r, c) for r in range(size) for c in range(size)]
    groups = (
        [[(r, c) for c in range(size)] for r in range(size)],
        [[(r, c) for r in range(size)] for c in range(size)],
        [
            [(r, c) for r in range(top, top + rows) for c in range(left, left + cols)]
            for top in range(0, size, rows)
            for left in range(0, size, cols)
        ],
    )
    clashes = {(r, c) for r, c in cells if givens[r][c] and grid[r][c] != givens[r][c]}
    for name, lines in zip(("rows", "columns", "boxes"), groups, strict=True):
        for line in lines:
            seen = {}
            for r, c in line:
                if grid[r][c]:
                    seen.setdefault(grid[r][c], []).append((r, c))
            repeats = [
                cell for found in seen.values() if len(found) > 1 for cell in found
            ]
            clashes.update(repeats)
            result[name] += not repeats
    result |= {
        "givens_kept": sum(
            1 for r, c in cells if givens[r][c] and grid[r][c] == givens[r][c]
        ),
        "filled": sum(1 for r, c in cells if grid[r][c]),
        "entries": sum(1 for r, c in cells if grid[r][c] and not givens[r][c]),
        "clashes": sorted([r, c] for r, c in clashes),
        "solved": check(Puzzle(size, tuple(map(tuple, givens)), None), grid),
    }
    return result


def session_record(turn):
    """A full log's free-time turn, as the compact record and the report keep
    it: session number, activity, the puzzle shown, the reply, its score."""
    prompt = (turn.get("messages") or [{}, {}])[-1].get("content", "")
    reply = (turn.get("parsed") or {}).get("text") or turn.get("reply") or ""
    givens = read_puzzle(prompt) if "Sudoku" in prompt else None
    record = {
        "session": turn.get("session"),
        "activity": "sudoku" if givens else "open",
        "reply": reply,
    }
    if givens:
        record |= {"puzzle": givens, "score": score(givens, reply)}
    return record
