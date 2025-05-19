# test_all.py

from board import Board
import moves


def sq(f, r):
    """Convert (file,rank) to algebraic notation, e.g. (1,1) → 'a1'."""
    return chr(ord("a") + f - 1) + str(r)


def assert_equal(a, b, msg=""):
    if a != b:
        raise AssertionError(f"{msg}: {a!r} != {b!r}")


def main():
    # 1) Test indexing helpers
    b = Board()
    assert_equal(b[(1, 1)], Board.EMPTY, "Empty at a1")
    assert_equal(b[(8, 8)], Board.EMPTY, "Empty at h8")
    b[(1, 1)] = "X"
    assert_equal(b[(1, 1)], "X", "Set/get a1")
    b[(1, 1)] = Board.EMPTY

    # 2) init_positions & __str__ format
    b.init_positions()
    lines = str(b).splitlines()
    assert lines[0].startswith(
        "8| r n b q k b n r"
    ), f"Back rank line mismatch: {lines[0]!r}"
    assert lines[-2] == " |----------------", f"Separator line mismatch: {lines[-2]!r}"
    assert (
        lines[-1].strip() == "a b c d e f g h"
    ), f"File labels mismatch: {lines[-1]!r}"

    # 3) Pawn single & double pushes
    w_moves = moves.pawn_moves(b, "white")
    b_moves = moves.pawn_moves(b, "black")
    w_push = [m for m in w_moves if m[2] is None]
    b_push = [m for m in b_moves if m[2] is None]
    assert_equal(len(w_push), 16, "White pawn advances")
    assert_equal(len(b_push), 16, "Black pawn advances")

    # 4) Pawn captures
    b = Board()
    b.init_positions()
    b.make_move((5, 2), (5, 4))  # e2→e4
    b.make_move((4, 7), (4, 5))  # d7→d5
    caps = moves.pawn_moves(b, "white")
    assert ((5, 4), (4, 5), None) in caps, "Capture e4→d5 missing"

    # 5) En passant
    b = Board()
    b.init_positions()
    # White pawn to d5
    b.make_move((4, 2), (4, 4))
    b.make_move((4, 4), (4, 5))
    # Black double-push c7→c5
    b.make_move((3, 7), (3, 5))
    assert_equal(b.en_passant_target, (3, 6), "EP target should be c6")
    ep_moves = moves.pawn_moves(b, "white")
    assert ((4, 5), (3, 6), None) in ep_moves, "EP move d5→c6 missing"
    # Execute EP capture
    b.make_move((4, 5), (3, 6), promo=None)
    assert_equal(b[(3, 5)], Board.EMPTY, "EP victim on c5 not removed")

    # 6) Promotion with explicit choice
    b = Board()
    b.init_positions()
    # White pawn on g7 → g8 promoting to Queen
    b[(7, 7)] = "P"
    b[(7, 2)] = b[(7, 8)] = Board.EMPTY
    b.make_move((7, 7), (7, 8), promo="Q")
    assert_equal(b[(7, 8)], "Q", "White promotion to Q on g8")

    b = Board()
    b.init_positions()
    # Black pawn on b2 → b1 promoting to knight
    b[(2, 2)] = "p"
    b[(2, 7)] = b[(2, 1)] = Board.EMPTY
    b.make_move((2, 2), (2, 1), promo="N")
    assert_equal(b[(2, 1)], "N", "Black promotion to N on b1")

    print("✔️ All tests passed!")


if __name__ == "__main__":
    main()
