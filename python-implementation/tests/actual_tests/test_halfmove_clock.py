# tests/test_halfmove_clock.py

from engine.board import Board
from engine.moves.move import Move
from engine.status import get_game_status


def test_halfmove_resets_on_pawn_move():
    b = Board()
    b.init_positions()
    b.halfmove_clock = 42
    b.make_move(Move((5, 2), (5, 4)))  # e2 → e4
    assert b.halfmove_clock == 0


def test_halfmove_resets_on_capture():
    b = Board()
    b.init_positions()
    b[(4, 4)] = "P"
    b[(5, 5)] = "p"
    b[(5, 2)] = b[(5, 7)] = b.EMPTY
    b.halfmove_clock = 50
    b.make_move(Move((4, 4), (5, 5)))  # capture
    assert b.halfmove_clock == 0


def test_halfmove_resets_on_en_passant():
    b = Board()
    b.init_positions()
    b[(4, 5)] = "P"
    b[(5, 5)] = b[(5, 7)] = "p"
    b[(4, 2)] = b[(5, 2)] = b[(5, 7)] = b.EMPTY
    b.en_passant_target = (5, 6)
    b.halfmove_clock = 77
    move = Move((4, 5), (5, 6), is_en_passant=True)
    b.make_move(move)
    assert b.halfmove_clock == 0


def test_halfmove_resets_on_promotion():
    b = Board()
    b[(1, 7)] = "P"
    b.halfmove_clock = 99
    move = Move((1, 7), (1, 8), promo="Q")
    b.make_move(move)
    assert b.halfmove_clock == 0


def test_halfmove_increments_on_quiet_move():
    b = Board()
    b.init_positions()
    b[(4, 4)] = "N"
    b[(4, 2)] = b.EMPTY
    b.halfmove_clock = 5
    b.make_move(Move((4, 4), (5, 6)))  # quiet move
    assert b.halfmove_clock == 6


def test_50_move_draw_triggers():
    b = Board()
    b[(4, 4)] = "K"
    b[(5, 5)] = "k"
    b.halfmove_clock = 100
    assert get_game_status(b, "white") == "draw by 50 moves"


def test_50_move_draw_not_triggered_at_99():
    b = Board()
    b[(4, 4)] = "K"
    b[(5, 5)] = "k"
    b.halfmove_clock = 99
    assert get_game_status(b, "white") == "ongoing"
