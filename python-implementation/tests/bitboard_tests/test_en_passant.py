from engine.bitboard.board import Board
from engine.bitboard.move import Move
from engine.bitboard.constants import WHITE_PAWN, BLACK_PAWN


def test_en_passant_execution():
    board = Board()

    # --- Setup: clear all bitboards and place only a white pawn on d2 (sq=11)
    board.bitboards = [0] * 12
    board.bitboards[WHITE_PAWN] = 1 << 11
    board.update_occupancies()

    # --- 1) Double‐push d2->d4 (11->27)
    move1 = Move(src=11, dst=27, capture=False)
    board.make_move(move1)

    # ep_square should now be d3 (sq=19)
    assert board.ep_square == 19, f"expected d3 (sq=19), got {board.ep_square}"

    # --- 2) Place a black pawn on e4 (sq=28) for the capture
    board.bitboards[BLACK_PAWN] = 1 << 28
    board.update_occupancies()

    # --- 3) En-passant capture e4xd3
    move2 = Move(src=28, dst=19, capture=True)
    board.make_move(move2)

    # After the capture:
    #  - white pawn at d4 (sq=27) should be gone
    assert (board.bitboards[WHITE_PAWN] & (1 << 27)) == 0

    #  - black pawn should now occupy d3 (sq=19)
    assert (board.bitboards[BLACK_PAWN] & (1 << 19)) != 0

    #  - ep_square must be cleared after the capture
    assert board.ep_square is None

    #  - overall occupancy should match the one black pawn on d3
    assert board.white_occ == 0
    assert board.black_occ == (1 << 19)
    assert board.all_occ == (1 << 19)


def test_ep_cleared_on_non_double_push():
    board = Board()
    # Place a pawn on d2 and do a single push d2->d3
    board.bitboards = [0] * 12
    board.bitboards[WHITE_PAWN] = 1 << 11
    board.update_occupancies()
    m1 = Move(src=11, dst=19, capture=False)  # d2->d3
    board.make_move(m1)
    assert board.ep_square is None

    # Now do a knight move (or any other piece) and ensure ep stays zero
    # (pretend a knight on g1->f3)
    board.bitboards = [0] * 12
    KNIGHT = 1  # or use your WHITE_KNIGHT constant
    board.bitboards[KNIGHT] = 1 << 6  # g1
    board.update_occupancies()
    m2 = Move(src=6, dst=21, capture=False)  # g1->f3
    board.make_move(m2)
    assert board.ep_square is None


def test_black_double_push_sets_ep():
    board = Board()
    board.bitboards = [0] * 12
    board.bitboards[BLACK_PAWN] = 1 << 52  # e7 is square 52
    board.update_occupancies()
    m = Move(src=52, dst=36, capture=False)  # e7->e5
    board.make_move(m)
    assert board.ep_square == 44  # e6 is square 44


def test_black_ep_capture_execution():
    board = Board()
    # Setup white pawn on d5 (sq=27) and black pawn on e7 (52)
    board.bitboards = [0] * 12
    board.bitboards[WHITE_PAWN] = 1 << 27
    board.bitboards[BLACK_PAWN] = 1 << 52
    board.update_occupancies()

    # Black double-push to e5
    m1 = Move(src=52, dst=36, capture=False)
    board.make_move(m1)
    assert board.ep_square == 44  # e6

    # White does d5×e6 ep
    m2 = Move(src=27, dst=44, capture=True)
    board.make_move(m2)
    # black pawn on e5 (36) should be removed
    assert (board.bitboards[BLACK_PAWN] & (1 << 36)) == 0
    # white pawn now on e6 (44)
    assert (board.bitboards[WHITE_PAWN] & (1 << 44)) != 0
    # ep cleared
    assert board.ep_square is None
