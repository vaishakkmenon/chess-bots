from engine.board import Board
from engine.rules import in_check
from engine.moves.generator import legal_moves


def is_checkmate(board: Board, color: str) -> bool:
    return in_check(board, color) and not legal_moves(board, color)


def is_stalemate(board: Board, color: str) -> bool:
    return not in_check(board, color) and not legal_moves(board, color)


def is_draw_by_50(board: Board):
    return board.halfmove_clock >= 100


def get_game_status(board: Board, color: str) -> str:
    if is_draw_by_50(board):
        return "draw by 50 moves"
    if is_checkmate(board, color):
        return "checkmate"
    if is_stalemate(board, color):
        return "stalemate"
    return "ongoing"
