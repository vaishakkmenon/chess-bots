# tests/test_halfmove_clock.py

import pytest
from engine.mailbox.board import Board
from engine.mailbox.moves.move import Move
from engine.mailbox.zobrist import Zobrist
from engine.mailbox.status import get_game_status


@pytest.fixture
def zobrist():
    return Zobrist()


@pytest.fixture
def board(zobrist):
    b = Board(zobrist)
    b.init_positions()
    b.zobrist_hash = b.zobrist.compute_hash(b, "white")
    return b


def test_halfmove_resets_on_pawn_move(board):
    board.init_positions()
    board.halfmove_clock = 42
    board.make_move(Move((5, 2), (5, 4)))  # e2 → e4
    assert board.halfmove_clock == 0


def test_halfmove_resets_on_capture(board):
    board.init_positions()
    board[(4, 4)] = "P"
    board[(5, 5)] = "p"
    board[(5, 2)] = board[(5, 7)] = board.EMPTY
    board.halfmove_clock = 50
    board.make_move(Move((4, 4), (5, 5)))  # capture
    assert board.halfmove_clock == 0


def test_halfmove_resets_on_en_passant(board):
    board.init_positions()
    board[(4, 5)] = "P"
    board[(5, 5)] = board[(5, 7)] = "p"
    board[(4, 2)] = board[(5, 2)] = board[(5, 7)] = board.EMPTY
    board.en_passant_target = (5, 6)
    board.halfmove_clock = 77
    move = Move((4, 5), (5, 6), is_en_passant=True)
    board.make_move(move)
    assert board.halfmove_clock == 0


def test_halfmove_resets_on_promotion(board):
    board[(1, 7)] = "P"
    board.halfmove_clock = 99
    move = Move((1, 7), (1, 8), promo="Q")
    board.make_move(move)
    assert board.halfmove_clock == 0


def test_halfmove_increments_on_quiet_move(board):
    board.init_positions()
    board[(4, 4)] = "N"
    board[(4, 2)] = board.EMPTY
    board.halfmove_clock = 5
    board.make_move(Move((4, 4), (5, 6)))  # quiet move
    assert board.halfmove_clock == 6


def test_50_move_draw_triggers(board):
    board[(4, 4)] = "K"
    board[(5, 5)] = "k"
    board.halfmove_clock = 100
    assert get_game_status(board, "white") == "draw by 50 moves"


def test_50_move_draw_not_triggered_at_99(board):
    board[(4, 4)] = "K"
    board[(5, 5)] = "k"
    board.halfmove_clock = 99
    assert get_game_status(board, "white") == "ongoing"
