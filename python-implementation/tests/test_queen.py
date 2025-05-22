from engine.board import Board
from engine.moves.queen import queen_moves
from tests.utils import (
    make_board,
    assert_true,
    assert_equal,
    print_section,
)


def test_queen_center_moves():
    print_section("Queen Center Quiet + Capture")

    b = make_board({(4, 4): "Q", (4, 7): "p", (7, 4): "p"})
    qm = queen_moves(b, "white")
    quiet = [m for m in qm if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in qm if b[m.to_sq].islower()]
    assert_true(len(quiet) > 0, "Queen must have at least one quiet slide")
    assert_true(
        len(captures) > 0, "Queen must have at least one capture slide"
    )


def test_queen_blocked_diagonal():
    print_section("Queen Blocked Diagonally By Friend")

    b = make_board({(4, 4): "Q", (6, 6): "P"})
    qm = queen_moves(b, "white")
    assert_true(
        all(m.to_sq != (7, 7) for m in qm),
        "Queen must stop before friendly pawn on diagonal",
    )


def test_queen_blocked_straight():
    print_section("Queen Blocked on File/Rank By Friend")

    b = make_board({(4, 4): "Q", (4, 2): "P"})
    qm = queen_moves(b, "white")
    file_moves = [m.to_sq for m in qm if m.from_sq == (4, 4)]
    assert_true(
        all(t != (4, 1) for t in file_moves),
        "Queen must stop before friendly pawn on file",
    )


def test_queen_edge_of_board():
    print_section("Queen Edge-of-Board")

    b = make_board({(1, 8): "Q"})
    qm = queen_moves(b, "white")
    seen = {m.to_sq for m in qm}
    assert_true(
        all(1 <= f <= 8 and 1 <= r <= 8 for (f, r) in seen),
        "All queen moves must stay on-board",
    )


def test_queen_full_cross_and_diagonals():
    print_section("Queen Full Range From Center")

    b = make_board({(5, 5): "Q"})
    qm = queen_moves(b, "white")
    expected = set()

    for i in range(1, 9):
        if i != 5:
            expected.add((i, 5))  # same rank
            expected.add((5, i))  # same file

    for i in range(1, 8):
        if 5 + i <= 8 and 5 + i <= 8:
            expected.add((5 + i, 5 + i))  # NE
        if 5 - i >= 1 and 5 + i <= 8:
            expected.add((5 - i, 5 + i))  # NW
        if 5 + i <= 8 and 5 - i >= 1:
            expected.add((5 + i, 5 - i))  # SE
        if 5 - i >= 1 and 5 - i >= 1:
            expected.add((5 - i, 5 - i))  # SW

    seen = {m.to_sq for m in qm}
    assert_equal(
        seen, expected, "Queen must move fully along ranks/files/diagonals"
    )


def test_queen_surrounded_by_friends():
    print_section("Queen Surrounded by Friends")

    queen_pos = (4, 4)
    directions = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),  # rook directions
        (1, 1),
        (-1, 1),
        (1, -1),
        (-1, -1),  # bishop directions
    ]
    pieces = {queen_pos: "Q"}
    for dx, dy in directions:
        pieces[(queen_pos[0] + dx, queen_pos[1] + dy)] = "P"
    b = make_board(pieces)
    qm = queen_moves(b, "white")
    assert_equal(
        len(qm),
        0,
        "Queen should have no moves if surrounded by friendly pieces",
    )


def test_queen_surrounded_by_enemies():
    print_section("Queen Surrounded by Enemies")

    queen_pos = (4, 4)
    directions = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),  # rook directions
        (1, 1),
        (-1, 1),
        (1, -1),
        (-1, -1),  # bishop directions
    ]
    pieces = {queen_pos: "Q"}
    for dx, dy in directions:
        pieces[(queen_pos[0] + dx, queen_pos[1] + dy)] = "p"
    b = make_board(pieces)
    qm = queen_moves(b, "white")
    targets = {m.to_sq for m in qm}
    expected = {
        (queen_pos[0] + dx, queen_pos[1] + dy) for dx, dy in directions
    }
    assert_equal(
        targets, expected, "Queen should capture all adjacent enemies"
    )
