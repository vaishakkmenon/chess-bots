from engine.mailbox.board import Board
from engine.mailbox.moves.bishop import bishop_moves
from engine.mailbox.moves.generator import legal_moves
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


def test_bishop_stops_after_capture():
    # King on e1 for legality context
    b = make_board(
        {
            (5, 1): "K",
            (3, 1): "B",  # bishop c1
            (6, 4): "p",  # target f4
            (7, 5): "p",  # extra piece beyond (should be unreachable)
        }
    )
    bm = bishop_moves(b, "white")
    dests = {m.to_sq for m in bm}
    assert (6, 4) in dests, "Capture square must be included"
    assert (7, 5) not in dests, "Squares beyond first capture must be excluded"


def test_bishop_moves_limited_when_pinned():
    # Pin line: a5-b4-c3-d2-e1
    pieces = {
        (5, 1): "K",  # king e1
        (3, 3): "B",  # bishop c3 (pinned)
        (1, 5): "b",  # black bishop a5, the pinning piece
    }
    b = make_board(pieces)
    legal = [m for m in legal_moves(b, "white") if m.from_sq == (3, 3)]
    targets = {m.to_sq for m in legal}
    expected = {(2, 4), (4, 2), (1, 5)}  # along the diagonal only
    assert targets == expected, "Pinned bishop can slide only on the pin line"


def test_bishop_corner_h8_moves():
    b = make_board({(8, 8): "B"})
    bm = bishop_moves(b, "white")
    expected = {(i, i) for i in range(1, 8)}  # (7,7) down to (1,1)
    seen = {m.to_sq for m in bm}
    assert_equal(
        seen, expected, "Bishop at h8 must slide along SW diagonal only"
    )
