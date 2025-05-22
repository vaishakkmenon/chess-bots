from engine.board import Board
from engine.moves.knight import knight_moves
from tests.utils import (
    make_board,
    assert_true,
    print_section,
)


# ─── Knight Tests ───────────────────────────────────────────────────────────
def test_knight_moves():
    print_section("Knight Moves Tests")

    # center quiet & capture in one set
    b = make_board({(4, 4): "N", (6, 5): "p"})
    km = knight_moves(b, "white")
    # quiet moves = jumps to empty squares
    quiet = [m for m in km if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in km if b[m.to_sq].islower()]
    assert_true(
        len(quiet) > 0, "Knight must have at least one non-capture jump"
    )
    assert_true(
        len(captures) > 0, "Knight must have at least one capture jump"
    )

    print("✔️ Knight moves include both quiet and capture.")
