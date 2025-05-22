from engine.board import Board
from engine.moves.bishop import bishop_moves
from tests.utils import (
    make_board,
    assert_equal,
    assert_true,
    print_section,
)


# ─── Bishop Tests ────────────────────────────────────────────────────────────
def test_bishop_moves():
    print_section("Bishop Moves Tests")

    # 1) quiet + capture from center
    b = make_board({(4, 4): "B", (2, 2): "p"})
    bm = bishop_moves(b, "white")
    quiet = [m for m in bm if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in bm if b[m.to_sq].islower()]
    assert_true(len(quiet) > 0, "Bishop must have at least one diagonal quiet")
    assert_true(
        len(captures) > 0, "Bishop must have at least one diagonal capture"
    )

    # 2) blocked by friend
    b = make_board({(4, 4): "B", (6, 6): "P"})
    bm = bishop_moves(b, "white")
    # should NOT include any move landing on (7,7) or beyond
    assert_true(
        all(m.to_sq != (7, 7) for m in bm),
        "Bishop must stop before a friendly pawn at (6,6)",
    )

    # 3) edge-of-board no wrap
    b = make_board({(1, 1): "B"})
    bm = bishop_moves(b, "white")
    # only NE direction should produce moves (to 2,2 .. 8,8)
    expected = {(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)}
    seen = {m.to_sq for m in bm}
    assert_equal(
        seen,
        expected - {(1, 1)},
        "Bishop at a1 must slide along one diagonal only",
    )

    print("✔️ Bishop slides pass quiet, capture, block & edge tests.")
