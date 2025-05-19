# engine/moves/all_moves.py
from .pawn import pawn_moves
from .knight import knight_moves


def all_moves(board, color):
    moves = []
    moves.extend(pawn_moves(board, color))
    moves.extend(knight_moves(board, color))
    return moves
