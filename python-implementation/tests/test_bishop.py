from engine.board import Board
from engine.moves.bishop import bishop_moves
from tests.utils import (
    make_board,
    assert_true,
    assert_equal,
    print_section,
)


def test_bishop_center_moves():
    print_section("Bishop Center Quiet + Capture")

    b = make_board({(4, 4): "B", (2, 2): "p"})
    bm = bishop_moves(b, "white")
    quiet = [m for m in bm if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in bm if b[m.to_sq].islower()]

    assert_true(len(quiet) > 0, "Bishop must have at least one diagonal quiet")
    assert_true(
        len(captures) > 0, "Bishop must have at least one diagonal capture"
    )


def test_bishop_blocked_by_friend():
    print_section("Bishop Blocked By Friend")

    b = make_board({(4, 4): "B", (6, 6): "P"})
    bm = bishop_moves(b, "white")
    blocked_target = (7, 7)
    assert_true(
        all(m.to_sq != blocked_target for m in bm),
        "Bishop must stop before a friendly pawn at (6,6)",
    )


def test_bishop_edge_of_board():
    print_section("Bishop Edge-of-Board")

    b = make_board({(1, 1): "B"})
    bm = bishop_moves(b, "white")
    expected = {(i, i) for i in range(2, 9)}  # (2,2) to (8,8)
    seen = {m.to_sq for m in bm}
    assert_equal(
        seen,
        expected,
        "Bishop at a1 must slide along NE diagonal only",
    )


def test_bishop_full_diagonals():
    print_section("Bishop Full Diagonals")

    b = make_board({(5, 5): "B"})
    bm = bishop_moves(b, "white")
    seen = {m.to_sq for m in bm}
    expected = set()

    # Add NE, NW, SE, SW diagonals from (5,5)
    for i in range(1, 8):
        if 5 + i <= 8 and 5 + i <= 8:
            expected.add((5 + i, 5 + i))  # NE
        if 5 - i >= 1 and 5 + i <= 8:
            expected.add((5 - i, 5 + i))  # NW
        if 5 + i <= 8 and 5 - i >= 1:
            expected.add((5 + i, 5 - i))  # SE
        if 5 - i >= 1 and 5 - i >= 1:
            expected.add((5 - i, 5 - i))  # SW

    assert_equal(seen, expected, "Bishop at e5 should see all 4 diagonals")


def test_bishop_surrounded_by_friends():
    print_section("Bishop Surrounded by Friends")

    bishop_pos = (4, 4)
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    pieces = {bishop_pos: "B"}
    for dx, dy in directions:
        pieces[(bishop_pos[0] + dx, bishop_pos[1] + dy)] = "P"
    b = make_board(pieces)
    bm = bishop_moves(b, "white")
    assert_equal(
        len(bm),
        0,
        "Bishop has no legal moves when all dirs are blocked by friends",
    )


def test_bishop_captures_only():
    print_section("Bishop Surrounded by Enemies")

    bishop_pos = (4, 4)
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    pieces = {bishop_pos: "B"}
    for dx, dy in directions:
        pieces[(bishop_pos[0] + dx, bishop_pos[1] + dy)] = "p"
    b = make_board(pieces)
    bm = bishop_moves(b, "white")
    targets = {m.to_sq for m in bm}
    expected = {(5, 5), (5, 3), (3, 5), (3, 3)}
    assert_equal(
        targets, expected, "Bishop should capture on all adjacent diagonals"
    )
