from engine.board import Board
from engine.moves.king import king_moves
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
