# engine/moves/all_moves.py
from engine.board import Board

from engine.rules import in_check
from typing import List

from engine.moves.move import Move
from engine.moves.pawn import pawn_moves
from engine.moves.knight import knight_moves
from engine.moves.bishop import bishop_moves
from engine.moves.rook import rook_moves
from engine.moves.queen import queen_moves
from engine.moves.king import king_moves


def all_moves(board: Board, color: str) -> List[Move]:
    moves = []
    moves.extend(pawn_moves(board, color))
    moves.extend(knight_moves(board, color))
    moves.extend(bishop_moves(board, color))
    moves.extend(rook_moves(board, color))
    moves.extend(queen_moves(board, color))
    moves.extend(king_moves(board, color))
    return moves


def legal_moves(board: Board, color: str) -> List[Move]:
    valid_moves = []
    moves = all_moves(board, color)
    for move in moves:
        rights, prev_halfmove = board.make_move(move)
        if not in_check(board, color):
            valid_moves.append(move)
        board.undo_move(move, rights, prev_halfmove)
    return valid_moves
