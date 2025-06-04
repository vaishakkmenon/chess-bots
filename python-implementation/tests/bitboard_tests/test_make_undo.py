import pytest
from copy import deepcopy

from engine.bitboard.board import Board
from engine.bitboard.move import Move
from engine.bitboard.constants import (
    WHITE_PAWN,
    BLACK_PAWN,
    WHITE,
    BLACK,
    WHITE_KNIGHT,
    WHITE_QUEEN,
    BLACK_ROOK,
)


def snapshot(board):
    return {
        "bitboards": deepcopy(board.bitboards),
        "ep_square": board.ep_square,
        "side": board.side_to_move,
        "white_occ": board.white_occ,
        "black_occ": board.black_occ,
        "all_occ": board.all_occ,
    }


def restore_ok(board, snap):
    assert board.bitboards == snap["bitboards"]
    assert board.ep_square == snap["ep_square"]
    assert board.side_to_move == snap["side"]
    assert board.white_occ == snap["white_occ"]
    assert board.black_occ == snap["black_occ"]
    assert board.all_occ == snap["all_occ"]


def test_simple_move_undo():
    board = Board()
    board.bitboards = [0] * 12
    board.bitboards[WHITE_PAWN] = 1 << 12  # e2
    board.update_occupancies()
    board.side_to_move = WHITE

    before = snapshot(board)
    mv = Move(src=12, dst=28, capture=False)  # e2->e4
    board.make_move(mv)
    board.undo_move()
    restore_ok(board, before)


def test_non_capture_knight_move_undo():
    board = Board()
    board.bitboards = [0] * 12
    board.bitboards[WHITE_KNIGHT] = 1 << 6  # g1
    board.update_occupancies()
    board.side_to_move = WHITE

    before = snapshot(board)
    mv = Move(src=6, dst=21, capture=False)  # g1->f3
    board.make_move(mv)
    board.undo_move()
    restore_ok(board, before)


def test_capture_move_undo():
    board = Board()
    board.bitboards = [0] * 12
    board.bitboards[WHITE_PAWN] = 1 << 27  # d4
    board.bitboards[BLACK_PAWN] = 1 << 36  # e5
    board.update_occupancies()
    board.side_to_move = WHITE

    before = snapshot(board)
    mv = Move(src=27, dst=36, capture=True)  # d4xe5
    board.make_move(mv)
    # sanity check the capture happened
    assert (board.bitboards[WHITE_PAWN] & (1 << 36)) != 0
    assert (board.bitboards[BLACK_PAWN] & (1 << 36)) == 0

    board.undo_move()
    restore_ok(board, before)


def test_en_passant_undo():
    board = Board()
    board.bitboards = [0] * 12
    board.bitboards[BLACK_PAWN] = 1 << 52  # e7
    board.bitboards[WHITE_PAWN] = 1 << 35  # d5
    board.update_occupancies()
    board.side_to_move = BLACK

    # Black double-push e7->e5
    before1 = snapshot(board)
    mv1 = Move(src=52, dst=36, capture=False)
    board.make_move(mv1)
    assert board.ep_square == (1 << 44)  # e6

    # White en-passant d5->e6
    before2 = snapshot(board)
    mv2 = Move(src=35, dst=44, capture=True, en_passant=True)
    board.make_move(mv2)
    assert (board.bitboards[WHITE_PAWN] & (1 << 44)) != 0
    assert (board.bitboards[BLACK_PAWN] & (1 << 36)) == 0

    # Undo ep-capture only
    board.undo_move()
    restore_ok(board, before2)

    # Undo double-push
    board.undo_move()
    restore_ok(board, before1)


def test_ep_cleared_on_non_double_push_and_undo():
    board = Board()
    board.bitboards = [0] * 12
    board.bitboards[WHITE_PAWN] = 1 << 12  # e2
    board.update_occupancies()
    board.side_to_move = WHITE

    # Single push clears ep_square
    before = snapshot(board)
    mv = Move(src=12, dst=20, capture=False)  # e2->e3
    board.make_move(mv)
    assert board.ep_square == 0
    board.undo_move()
    restore_ok(board, before)

    # Non-pawn move doesn't create ep_square
    board.bitboards = [0] * 12
    board.bitboards[WHITE_KNIGHT] = 1 << 1  # b1
    board.update_occupancies()
    board.side_to_move = WHITE
    before2 = snapshot(board)
    mv2 = Move(src=1, dst=18, capture=False)  # b1->c3
    board.make_move(mv2)
    assert board.ep_square == 0
    board.undo_move()
    restore_ok(board, before2)


def test_undo_without_history_raises():
    board = Board()
    with pytest.raises(IndexError):
        board.undo_move()


def test_pawn_promotion_round_trip():
    board = Board()
    board.bitboards = [0] * 12
    board.bitboards[WHITE_PAWN] = 1 << 48  # a7
    board.update_occupancies()
    board.side_to_move = WHITE

    before = snapshot(board)
    mv = Move(src=48, dst=56, capture=False, promotion="Q")
    board.make_move(mv)
    assert board.bitboards[WHITE_PAWN] == 0
    assert (board.bitboards[WHITE_QUEEN] & (1 << 56)) != 0
    board.undo_move()
    restore_ok(board, before)


def test_capture_promotion_round_trip():
    board = Board()
    board.bitboards = [0] * 12
    board.bitboards[WHITE_PAWN] = 1 << 54  # g7
    board.bitboards[BLACK_ROOK] = 1 << 63  # h8
    board.update_occupancies()
    board.side_to_move = WHITE

    before = snapshot(board)
    mv = Move(src=54, dst=63, capture=True, promotion="Q")
    board.make_move(mv)
    assert board.bitboards[WHITE_PAWN] == 0
    assert (board.bitboards[WHITE_QUEEN] & (1 << 63)) != 0
    assert (board.bitboards[BLACK_ROOK] & (1 << 63)) == 0

    board.undo_move()
    restore_ok(board, before)
