# tests/test_insufficient_material.py

import pytest
from engine.mailbox.board import Board
from engine.mailbox.zobrist import Zobrist
from engine.mailbox.status import is_draw_by_insufficient_material


def make_board(pieces: dict[tuple[int, int], str]) -> Board:
    """
    Build a board with exactly the given {(file, rank): piece} map.
    """
    b = Board(Zobrist())
    # clear out everything
    b.squares = [[b.EMPTY for _ in range(b.FILES)] for _ in range(b.RANKS)]
    for pos, p in pieces.items():
        b[pos] = p
    return b


@pytest.mark.parametrize(
    "white,black,expected",
    [
        # King vs King
        ([("K", (5, 1))], [("k", (5, 8))], True),
        # King+Knight vs King
        ([("K", (5, 1)), ("N", (2, 1))], [("k", (5, 8))], True),
        ([("K", (5, 1))], [("k", (5, 8)), ("n", (2, 8))], True),
        # King+Bishop vs King
        ([("K", (5, 1)), ("B", (3, 1))], [("k", (5, 8))], True),
        ([("K", (5, 1))], [("k", (5, 8)), ("b", (3, 8))], True),
        # King+Bishop vs King+Bishop, same‐color bishops
        ([("K", (5, 1)), ("B", (3, 1))], [("k", (5, 8)), ("b", (6, 6))], True),
        # King+Bishop vs King+Bishop, opposite‐color bishops
        ([("K", (5, 1)), ("B", (3, 1))], [("k", (5, 8)), ("b", (6, 5))], True),
        # King+Two Knights vs King → draw
        ([("K", (5, 1)), ("N", (2, 1)), ("N", (7, 1))], [("k", (5, 8))], True),
        # Any other material → not insufficient
        ([("K", (5, 1)), ("P", (4, 2))], [("k", (5, 8))], False),
        (
            [("K", (5, 1)), ("B", (3, 1)), ("N", (6, 1))],
            [("k", (5, 8))],
            False,
        ),
        ([("K", (5, 1))], [("k", (5, 8)), ("q", (1, 8))], False),
    ],
)
def test_insufficient(white, black, expected):
    # build a position map {(file, rank): "piece"}
    pieces: dict[tuple[int, int], str] = {}
    for p, pos in white:
        pieces[pos] = p
    for p, pos in black:
        pieces[pos] = p
    b = make_board(pieces)
    assert is_draw_by_insufficient_material(b) is expected
