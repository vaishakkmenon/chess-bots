# Ignoring type checking import suggestion because it is not necessary
from engine.board import Board  # noqa: TC002
from engine.rules import in_check
from engine.moves.generator import legal_moves

from collections import Counter


def is_checkmate(board: Board, color: str) -> bool:
    return in_check(board, color) and not legal_moves(board, color)


def is_stalemate(board: Board, color: str) -> bool:
    return not in_check(board, color) and not legal_moves(board, color)


def is_draw_by_50(board: Board):
    return board.halfmove_clock >= 100


def is_draw_by_repetition(board: Board, *, count: int = 3) -> bool:
    print(board.history)
    freqs = Counter(board.history)
    # If any hash hits the threshold, we have repetition draw.
    return any(freq >= count for freq in freqs.values())


def get_game_status(board: Board, color: str) -> str:
    rep_count = Counter(board.history)[board.zobrist_hash]
    if rep_count >= 5:
        return "draw by 5 fold repetition"
    if rep_count >= 3:
        return "draw by 3 fold repetition"
    if is_draw_by_50(board):
        return "draw by 50 moves"
    if is_checkmate(board, color):
        return "checkmate"
    if is_stalemate(board, color):
        return "stalemate"
    return "ongoing"
