# tests/test_fullmove_number.py

from engine.board import Board
from engine.moves.move import Move


def test_initial_fullmove_number_is_1():
    b = Board()
    assert b.fullmove_number == 1


def test_white_move_does_not_increment_fullmove():
    b = Board()
    b.init_positions()
    b.make_move(Move((5, 2), (5, 4)))  # e2 → e4
    assert b.fullmove_number == 1


def test_black_move_increments_fullmove():
    b = Board()
    b.init_positions()
    rights1, clock1 = b.make_move(Move((5, 2), (5, 4)))  # white
    rights2, clock2 = b.make_move(Move((5, 7), (5, 5)))  # black
    assert b.fullmove_number == 2


def test_undo_restores_fullmove_number():
    b = Board()
    b.init_positions()
    move1 = Move((5, 2), (5, 4))  # white
    move2 = Move((5, 7), (5, 5))  # black
    rights1, clock1 = b.make_move(move1)
    rights2, clock2 = b.make_move(move2)
    assert b.fullmove_number == 2

    b.undo_move(move2, rights2, clock2)  # undo black move
    assert b.fullmove_number == 1

    b.undo_move(move1, rights1, clock1)  # undo white move
    assert b.fullmove_number == 1
