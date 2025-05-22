from engine.board import Board
from engine.moves.queen import queen_moves
from tests.utils import (
    make_board,
    assert_true,
    print_section,
)


# ─── Queen Tests ─────────────────────────────────────────────────────────────
def test_queen_moves():
    print_section("Queen Moves Tests")

    # 1) quiet + capture from center
    b = make_board({(4, 4): "Q", (4, 7): "p", (7, 4): "p"})
    qm = queen_moves(b, "white")
    quiet = [m for m in qm if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in qm if b[m.to_sq].islower()]
    assert_true(len(quiet) > 0, "Queen must have at least one quiet slide")
    assert_true(
        len(captures) > 0, "Queen must have at least one capture slide"
    )

    # 2) diagonal block by friend (use a pawn so only one queen is tested)
    b = make_board({(4, 4): "Q", (6, 6): "P"})
    qm = queen_moves(b, "white")
    # only slides up to (5,5), but not (6,6) or beyond
    assert_true(
        all(m.to_sq != (7, 7) for m in qm),
        "Queen must stop before friendly pawn on diagonal",
    )

    # 3) file/rank block by friend (use a pawn)
    b = make_board({(4, 4): "Q", (4, 2): "P"})
    qm = queen_moves(b, "white")
    # only slides down to (4,3), but not (4,2) or (4,1)
    file_moves = [m.to_sq for m in qm if m.from_sq == (4, 4)]
    assert_true(
        all(t != (4, 1) for t in file_moves),
        "Queen must stop before friendly pawn on file",
    )

    # 4) edge-of-board no wrap
    b = make_board({(1, 8): "Q"})
    qm = queen_moves(b, "white")
    seen = {m.to_sq for m in qm}
    assert_true(
        all(1 <= f <= 8 and 1 <= r <= 8 for (f, r) in seen),
        "All queen moves must stay on-board",
    )

    print("✔️ Queen slides pass quiet, capture, block & edge tests.")
