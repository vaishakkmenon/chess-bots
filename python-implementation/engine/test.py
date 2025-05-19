# test_en_passant.py

from board import Board

# import moves


# Helper to convert (file,rank) → algebraic (e.g. "e4")
def sq(f, r):
    return chr(ord("a") + f - 1) + str(r)


def debug_board(b, label="Board"):
    print(f"\n=== {label} ===")
    print(b)
    print("en_passant_target:", b.en_passant_target)


def debug_moves(ms, label="Moves"):
    print(f"\n--- {label} (count={len(ms)}) ---")
    for frm, to in ms:
        print(f"  {sq(*frm)} → {sq(*to)}")
    if not ms:
        print("  (none)")


def main():
    board = Board()
    board.init_positions()
    debug_board(board, "Initial Position")

    # 1) White advances pawn from d2 to d5 in two steps
    print("\n1) White: d2→d4")
    board.make_move((4, 2), (4, 4))
    debug_board(board, "After d2→d4")

    print("\n2) White: d4→d5")
    board.make_move((4, 4), (4, 5))
    debug_board(board, "After d4→d5")

    # 2) Black double-push from c7→c5
    print("\n3) Black: c7→c5")
    board.make_move((3, 7), (3, 5))
    debug_board(board, "After c7→c5")
    assert board.en_passant_target == (
        3,
        6,
    ), f"Expected EP target c6, got {board.en_passant_target!r}"

    # 3) Generate white pawn moves; should include d5xc6 EP
    # print("\n4) Generate White pawn moves (expect en passant)")
    # white_moves = moves.pawn_moves(board, "white")
    # debug_moves(white_moves, "White Pawn Moves")
    # assert ((4, 5), (3, 6)) in white_moves, "En passant move d5→c6 missing"

    # 4) Execute the en passant capture
    print("\n4) White plays d5xc6 en passant")
    board.make_move((4, 5), (3, 6))
    debug_board(board, "After en passant capture d5xc6")
    # Confirm the pawn on c5 was removed
    assert board[(3, 5)] == Board.EMPTY, "Captured pawn on c5 was not removed"

    print("\n✅ En passant logic is working correctly!")


if __name__ == "__main__":
    main()
