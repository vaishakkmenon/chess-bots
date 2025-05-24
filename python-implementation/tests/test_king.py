from engine.board import Board
from engine.moves.king import king_moves
from engine.moves.generator import legal_moves
from tests.utils import (
    make_board,
    assert_true,
    assert_equal,
    print_section,
)


def test_king_center_moves():
    print_section("King Basic Center Moves")

    b = make_board({(4, 4): "K", (5, 5): "p"})
    b.white_can_castle_kingside = False
    b.white_can_castle_queenside = False

    km = king_moves(b, "white")
    quiet = [m for m in km if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in km if b[m.to_sq].islower()]

    assert_true(len(quiet) == 7, "King should have 7 quiet squares")
    assert_true(len(captures) == 1, "King should be able to capture 1 enemy")


def test_king_edge_moves():
    print_section("King Edge-of-Board Moves")

    b = make_board({(1, 1): "K"})
    b.white_can_castle_kingside = False
    b.white_can_castle_queenside = False
    km = king_moves(b, "white")

    expected = {(1, 2), (2, 2), (2, 1)}
    seen = {m.to_sq for m in km}
    assert_equal(seen, expected, "King on a1 should only have 3 legal moves")


def test_king_blocked_by_friends():
    print_section("King Blocked By Friends")

    b = make_board(
        {
            (4, 4): "K",
            (3, 4): "P",
            (5, 4): "P",
            (3, 5): "P",
            (4, 5): "P",
            (5, 5): "P",
            (3, 3): "P",
            (4, 3): "P",
            (5, 3): "P",
        }
    )
    b.white_can_castle_kingside = False
    b.white_can_castle_queenside = False

    km = king_moves(b, "white")
    assert_equal(
        len(km), 0, "King should have 0 legal moves when surrounded by friends"
    )


def test_king_surrounded_by_enemies():
    print_section("King Surrounded by Enemies")

    b = make_board(
        {
            (4, 4): "K",
            (3, 4): "p",
            (5, 4): "p",
            (3, 5): "p",
            (4, 5): "p",
            (5, 5): "p",
            (3, 3): "p",
            (4, 3): "p",
            (5, 3): "p",
        }
    )
    b.white_can_castle_kingside = False
    b.white_can_castle_queenside = False

    km = king_moves(b, "white")
    targets = {m.to_sq for m in km}
    expected = {(3, 4), (5, 4), (3, 5), (4, 5), (5, 5), (3, 3), (4, 3), (5, 3)}
    assert_equal(
        targets, expected, "King should capture all surrounding enemies"
    )


def _dests(board, frm):
    return {m.to_sq for m in legal_moves(board, "white") if m.from_sq == frm}


def test_king_cannot_step_into_check():
    b = make_board({(5, 4): "K", (5, 8): "r"})
    assert (5, 5) not in _dests(b, (5, 4))


def test_kings_not_adjacent():
    b = make_board({(5, 4): "K", (6, 6): "k"})
    # Square (6,5) would place the kings adjacent
    assert (6, 5) not in _dests(b, (5, 4))


def test_king_must_escape_check():
    # Black rook gives check on the e-file
    b = make_board({(5, 1): "K", (5, 8): "r"})
    escapes = {m.to_sq for m in legal_moves(b, "white") if m.from_sq == (5, 1)}
    expected = {(4, 1), (6, 1), (4, 2), (6, 2)}  # d1, f1, d2, f2
    assert escapes == expected


def test_king_cannot_capture_defended_piece():
    b = make_board({(5, 1): "K", (4, 2): "p", (4, 8): "r"})  # pawn d2, rook d8
    king_dests = {
        m.to_sq for m in legal_moves(b, "white") if m.from_sq == (5, 1)
    }
    assert (
        4,
        2,
    ) not in king_dests, "King must not capture into a checked square"


def test_king_double_check_only_king_moves():
    b = make_board(
        {(5, 1): "K", (5, 8): "r", (8, 4): "b"}
    )  # rook e8 & bishop h4
    legal = legal_moves(b, "white")
    non_king = [m for m in legal if b[m.from_sq] != "K"]
    assert non_king == [], "In double check only king moves are legal"
