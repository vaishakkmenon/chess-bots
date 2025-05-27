from engine.mailbox.board import Board
from engine.mailbox.moves.knight import knight_moves
from engine.mailbox.moves.generator import legal_moves
from tests.utils import (
    make_board,
    assert_true,
    assert_equal,
    print_section,
)


def test_knight_center_moves():
    print_section("Knight Center Quiet + Capture")

    # Knight on d4 (4,4) with black pawn on f5 (6,5)
    b = make_board({(4, 4): "N", (6, 5): "p"})
    km = knight_moves(b, "white")

    quiet = [m for m in km if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in km if b[m.to_sq].islower()]

    assert_true(len(quiet) > 0, "Knight must have quiet moves from center")
    assert_true(len(captures) > 0, "Knight must have capture move on f5")


def test_knight_edge_moves():
    print_section("Knight Edge-of-Board Test")

    # Knight on a1 (1,1), should only have 2 legal jumps: b3 and c2
    b = make_board({(1, 1): "N"})
    km = knight_moves(b, "white")
    targets = {m.to_sq for m in km}
    expected = {(2, 3), (3, 2)}  # b3 and c2

    assert_equal(targets, expected, "Knight at a1 must only jump to b3 and c2")


def test_knight_blocked_by_friends():
    print_section("Knight Blocked By Friend Test")

    # Knight at d4, friendly pawns on all 8 potential squares
    knight_pos = (4, 4)
    targets = [(3, 6), (5, 6), (6, 5), (6, 3), (5, 2), (3, 2), (2, 3), (2, 5)]
    pieces = {knight_pos: "N"}
    pieces.update({sq: "P" for sq in targets})  # all friendlies
    b = make_board(pieces)
    km = knight_moves(b, "white")
    assert_equal(
        len(km), 0, "Knight should have no legal jumps through friendly units"
    )


def test_knight_captures_only():
    print_section("Knight Capture Only Test")

    # Knight on d4, enemy pieces only
    knight_pos = (4, 4)
    targets = [(3, 6), (5, 6), (6, 5), (6, 3), (5, 2), (3, 2), (2, 3), (2, 5)]
    pieces = {knight_pos: "N"}
    pieces.update({sq: "p" for sq in targets})  # all enemies
    b = make_board(pieces)
    km = knight_moves(b, "white")

    assert_equal(
        len(km),
        8,
        "Knight should have 8 capture moves when surrounded by enemies",
    )


def test_knight_mixed_moves():
    print_section("Knight Mixed Quiet and Capture")

    # Knight on d4, 4 quiets, 4 captures
    knight_pos = (4, 4)
    quiet_sqs = [(2, 3), (3, 2), (6, 3), (5, 2)]
    capture_sqs = [(2, 5), (3, 6), (5, 6), (6, 5)]
    pieces = {knight_pos: "N"}
    pieces.update({sq: "." for sq in quiet_sqs})
    pieces.update({sq: "p" for sq in capture_sqs})
    b = make_board(pieces)
    km = knight_moves(b, "white")

    quiet = [m.to_sq for m in km if b[m.to_sq] == Board.EMPTY]
    captures = [m.to_sq for m in km if b[m.to_sq].islower()]

    assert_equal(
        set(quiet), set(quiet_sqs), "Knight should have correct quiet squares"
    )
    assert_equal(
        set(captures),
        set(capture_sqs),
        "Knight should have correct capture squares",
    )


def test_knight_stays_on_board():
    b = make_board({(1, 2): "N", (5, 1): "K"})
    dests = {m.to_sq for m in knight_moves(b, "white")}
    assert all(1 <= x <= 8 and 1 <= y <= 8 for x, y in dests)


def test_pinned_knight_no_moves():
    b = make_board({(5, 1): "K", (5, 2): "N", (5, 8): "r"})
    legal = legal_moves(b, "white")
    assert all(m.from_sq != (5, 2) for m in legal)


def test_knight_jumps_over_blockers():
    b = make_board(
        {
            (5, 1): "K",  # king e1
            (2, 1): "N",  # knight b1
            (2, 2): "P",  # b2 blocker
            (3, 2): "P",  # c2 blocker
        }
    )
    dests = {m.to_sq for m in knight_moves(b, "white")}
    # Knight b1 should reach a3, c3, d2
    assert dests == {(1, 3), (3, 3), (4, 2)}


# 2 — knight pinned _horizontally_ cannot move
def test_knight_pinned_on_rank_no_moves():
    b = make_board(
        {
            (5, 1): "K",  # king e1
            (3, 1): "N",  # knight c1
            (8, 1): "r",  # black rook h1 pinning along rank 1
        }
    )
    legal = legal_moves(b, "white")
    assert all(
        m.from_sq != (3, 1) for m in legal
    ), "Rank-pinned knight must stay put"


def test_knight_pinned_on_diagonal_no_moves():
    # Diagonal b4-c3-d2-e1 pins the knight
    b = make_board(
        {
            (5, 1): "K",  # king e1
            (4, 2): "N",  # knight d2
            (2, 4): "b",  # black bishop b4
        }
    )
    assert all(
        m.from_sq != (4, 2) for m in legal_moves(b, "white")
    ), "Diagonal-pinned knight must stay put"
