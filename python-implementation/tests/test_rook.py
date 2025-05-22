from engine.board import Board
from engine.moves.rook import rook_moves
from tests.utils import (
    make_board,
    assert_equal,
    assert_true,
    print_section,
)


def test_rook_center_moves():
    print_section("Rook Center Quiet + Capture")

    b = make_board({(4, 4): "R", (4, 7): "p"})
    rm = rook_moves(b, "white")
    quiet = [m for m in rm if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in rm if b[m.to_sq].islower()]
    assert_true(len(quiet) > 0, "Rook must have at least one file/rank quiet")
    assert_true(
        len(captures) > 0, "Rook must have at least one file/rank capture"
    )


def test_rook_blocked_by_friend():
    print_section("Rook Blocked By Friend")

    b = make_board({(4, 4): "R", (4, 2): "P"})
    rm = rook_moves(b, "white")
    assert_true(
        all(m.to_sq != (4, 1) for m in rm),
        "Rook must stop before a friendly pawn at (4,2)",
    )


def test_rook_edge_of_board():
    print_section("Rook Edge-of-Board")

    b = make_board({(8, 8): "R"})
    rm = rook_moves(b, "white")
    expected = {(i, 8) for i in range(1, 9)} | {(8, i) for i in range(1, 9)}
    seen = {m.to_sq for m in rm}
    assert_equal(
        seen - {(8, 8)},
        expected - {(8, 8)},
        "Rook at h8 must slide along file h and rank 8 only",
    )


def test_rook_full_cross():
    print_section("Rook Full Cross from Center")

    b = make_board({(5, 5): "R"})
    rm = rook_moves(b, "white")
    expected = set()

    for i in range(1, 9):
        if i != 5:
            expected.add((i, 5))  # same rank
            expected.add((5, i))  # same file

    seen = {m.to_sq for m in rm}
    assert_equal(
        seen, expected, "Rook at e5 must move along full file and rank"
    )


def test_rook_surrounded_by_friends():
    print_section("Rook Surrounded by Friends")

    rook_pos = (4, 4)
    pieces = {
        rook_pos: "R",
        (4, 3): "P",
        (4, 5): "P",  # up/down
        (3, 4): "P",
        (5, 4): "P",  # left/right
    }
    b = make_board(pieces)
    rm = rook_moves(b, "white")
    assert_equal(
        len(rm),
        0,
        "Rook should have no moves if surrounded by friendly pieces",
    )


def test_rook_captures_only():
    print_section("Rook Surrounded by Enemies")

    rook_pos = (4, 4)
    pieces = {
        rook_pos: "R",
        (4, 3): "p",
        (4, 5): "p",  # up/down
        (3, 4): "p",
        (5, 4): "p",  # left/right
    }
    b = make_board(pieces)
    rm = rook_moves(b, "white")
    targets = {m.to_sq for m in rm}
    expected = {(4, 3), (4, 5), (3, 4), (5, 4)}
    assert_equal(
        targets,
        expected,
        "Rook should be able to capture in all four directions",
    )
