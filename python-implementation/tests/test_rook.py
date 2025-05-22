from engine.board import Board
from engine.moves.rook import rook_moves
from tests.utils import (
    make_board,
    assert_equal,
    assert_true,
    print_section,
)


# ─── Rook Tests ──────────────────────────────────────────────────────────────
def test_rook_moves():
    print_section("Rook Moves Tests")

    # 1) quiet + capture from center
    b = make_board({(4, 4): "R", (4, 7): "p"})
    rm = rook_moves(b, "white")
    quiet = [m for m in rm if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in rm if b[m.to_sq].islower()]
    assert_true(len(quiet) > 0, "Rook must have at least one file/rank quiet")
    assert_true(
        len(captures) > 0, "Rook must have at least one file/rank capture"
    )

    # 2) blocked by friend
    b = make_board({(4, 4): "R", (4, 2): "P"})
    rm = rook_moves(b, "white")
    # should NOT include any move to (4,1)
    assert_true(
        all(m.to_sq != (4, 1) for m in rm),
        "Rook must stop before a friendly pawn at (4,2)",
    )

    # 3) edge-of-board no wrap
    b = make_board({(8, 8): "R"})
    rm = rook_moves(b, "white")
    # only W and S directions: ranks 1–8 at file=8 and files 1–8 at rank=8
    expected = {(i, 8) for i in range(1, 9)} | {(8, i) for i in range(1, 9)}
    seen = {m.to_sq for m in rm}
    # remove starting square:
    assert_equal(
        seen,
        expected - {(8, 8)},
        "Rook at h8 must slide along file h and rank 8 only",
    )

    print("✔️ Rook slides pass quiet, capture, block & edge tests.")
