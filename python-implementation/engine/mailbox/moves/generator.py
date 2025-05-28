# engine/moves/all_moves.py
from engine.mailbox.board import Board  # noqa: TC002

from engine.mailbox.rules import in_check
from typing import List

from engine.mailbox.moves.move import Move  # noqa: TC002
from engine.mailbox.moves.pawn import pawn_moves
from engine.mailbox.moves.knight import knight_moves
from engine.mailbox.moves.bishop import bishop_moves
from engine.mailbox.moves.rook import rook_moves
from engine.mailbox.moves.queen import queen_moves
from engine.mailbox.moves.king import king_moves


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
