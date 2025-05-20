# engine/moves/all_moves.py
from .pawn import pawn_moves
from .knight import knight_moves
from .bishop import bishop_moves
from .rook import rook_moves
from .queen import queen_moves
from .king import king_moves


def all_moves(board, color):
    moves = []
    moves.extend(pawn_moves(board, color))
    moves.extend(knight_moves(board, color))
    moves.extend(bishop_moves(board, color))
    moves.extend(rook_moves(board, color))
    moves.extend(queen_moves(board, color))
    moves.extend(king_moves(board, color))
    return moves
