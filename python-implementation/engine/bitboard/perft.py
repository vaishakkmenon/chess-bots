from typing import Dict
from engine.bitboard.move import Move  # noqa:TC002
from engine.bitboard.board import Board  # noqa:TC002
from engine.bitboard.generator import generate_legal_moves


def perft(board: Board, depth: int) -> int:

    if depth == 0:
        return 1
    nodes = 0
    for move in generate_legal_moves(board):
        board.make_move(move)
        nodes += perft(board, depth - 1)
        board.undo_move()
    return nodes


def perft_divide(board: Board, depth: int) -> Dict[Move, int]:
    if depth == 0:
        return 1

    results = {}
    for move in generate_legal_moves(board):
        board.make_move(move)
        results[move] = perft(board, depth - 1)
        board.undo_move()
    return results
