from engine.board import Board
from engine.moves.king import king_moves
from tests.utils import (
    make_board,
    assert_true,
    print_section,
)


# ─── King Tests ──────────────────────────────────────────────────────────────
def test_king_moves():
    print_section("King Basic Moves")

    # King in center with one enemy
    b = make_board({(4, 4): "K", (5, 5): "p"})
    # manually disable castling for now
    b.white_can_castle_kingside = False
    b.white_can_castle_queenside = False

    km = king_moves(b, "white")
    quiet = [m for m in km if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in km if b[m.to_sq].islower()]

    assert_true(
        len(quiet) == 7,
        "King on an empty 8x8 minus one enemy should have 7 quiet",
    )
    assert_true(
        len(captures) == 1,
        "King must be able to capture the one enemy at (5,5)",
    )

    print("✔️ King basic quiet + capture moves pass.")
