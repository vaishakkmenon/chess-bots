from engine.mailbox.board import Board
from engine.mailbox.moves.move import Move
from engine.mailbox.moves.rook import rook_moves
from engine.mailbox.moves.generator import legal_moves
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


def _dests_from(b, frm):
    return {m.to_sq for m in rook_moves(b, "white") if m.from_sq == frm}


def test_rook_stops_on_first_enemy():
    b = make_board({(5, 1): "K", (4, 4): "R", (4, 7): "p"})
    dests = _dests_from(b, (4, 4))
    assert (4, 7) in dests and (4, 8) not in dests


def test_rook_move_turns_off_castling_flag():
    b = make_board({(1, 1): "R"})
    b.white_can_castle_queenside = True
    m = Move((1, 1), (1, 2))
    rights, prev_halfclock = b.make_move(m)
    assert not b.white_can_castle_queenside
    b.undo_move(m, rights, prev_halfclock)
    assert b.white_can_castle_queenside


def test_rook_vertical_pin_stays_on_file():
    # Black rook on e8 pins white rook on e3 to the white king on e1.
    b = make_board({(5, 1): "K", (5, 3): "R", (5, 8): "r"})
    moves = [m for m in legal_moves(b, "white") if m.from_sq == (5, 3)]
    # Rook may move only up or down the e‑file
    assert moves and all(m.to_sq[0] == 5 for m in moves)


def test_rook_horizontal_pin_stays_on_rank():
    # Pin line a1–b1–c1–d1–e1 (king)
    b = make_board(
        {(5, 1): "K", (3, 1): "R", (1, 1): "r"}
    )  # king e1, rook c1, black rook a1
    rook_moves_only = [
        m for m in legal_moves(b, "white") if m.from_sq == (3, 1)
    ]
    assert all(
        m.to_sq[1] == 1 for m in rook_moves_only
    ), "Pinned rook must not leave rank 1"


def test_rook_cannot_move_when_diagonally_pinned():
    # Pin line: c3-d2-e1
    b = make_board(
        {(5, 1): "K", (4, 2): "R", (3, 3): "b"}
    )  # king e1, rook d2, bishop c3
    assert all(m.from_sq != (4, 2) for m in legal_moves(b, "white"))


def test_rook_stops_after_horizontal_capture():
    b = make_board(
        {(5, 1): "K", (4, 4): "R", (7, 4): "p"}
    )  # rook d4, enemy pawn g4
    dests = {m.to_sq for m in rook_moves(b, "white") if m.from_sq == (4, 4)}
    assert (7, 4) in dests and (8, 4) not in dests
