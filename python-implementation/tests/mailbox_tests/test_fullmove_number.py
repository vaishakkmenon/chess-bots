# tests/test_fullmove_number.py

import pytest
from engine.mailbox.board import Board
from engine.mailbox.zobrist import Zobrist
from engine.mailbox.moves.move import Move


@pytest.fixture
def zobrist():
    return Zobrist()


@pytest.fixture
def board(zobrist):
    b = Board(zobrist)
    b.init_positions()
    b.zobrist_hash = b.zobrist.compute_hash(b, "white")
    return b


def test_initial_fullmove_number_is_1(board):
    assert board.fullmove_number == 1


def test_white_move_does_not_increment_fullmove(board):

    board.init_positions()
    board.make_move(Move((5, 2), (5, 4)))  # e2 → e4
    assert board.fullmove_number == 1


def test_black_move_increments_fullmove(board):

    board.init_positions()
    rights1, clock1 = board.make_move(Move((5, 2), (5, 4)))  # white
    rights2, clock2 = board.make_move(Move((5, 7), (5, 5)))  # black
    assert board.fullmove_number == 2


def test_undo_restores_fullmove_number(board):

    board.init_positions()
    move1 = Move((5, 2), (5, 4))  # white
    move2 = Move((5, 7), (5, 5))  # black
    rights1, clock1 = board.make_move(move1)
    rights2, clock2 = board.make_move(move2)
    assert board.fullmove_number == 2

    board.undo_move(move2, rights2, clock2)  # undo black move
    assert board.fullmove_number == 1

    board.undo_move(move1, rights1, clock1)  # undo white move
    assert board.fullmove_number == 1
