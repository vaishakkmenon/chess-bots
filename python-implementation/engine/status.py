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


def is_draw_by_insufficient_material(board: Board) -> bool:
    white_minors = []
    black_minors = []

    for file in range(1, 9):
        for rank in range(1, 9):
            piece = board[(file, rank)]
            if piece == board.EMPTY or piece.upper() == "K":
                continue
            if piece.upper() in ("B", "N"):
                if piece.isupper():
                    white_minors.append((piece, (file + rank) % 2))
                else:
                    black_minors.append((piece, (file + rank) % 2))
            else:
                return False

    def side_insufficient(minors):
        if not minors:
            return True
        if len(minors) == 1:
            return True
        if len(minors) == 2 and all(p.upper() == "N" for p, _ in minors):
            return True
        if len(minors) == 2 and all(p.upper() == "B" for p, _ in minors):
            return minors[0][1] == minors[1][1]
        return False

    return side_insufficient(white_minors) and side_insufficient(black_minors)


def get_game_status(board: Board, color: str) -> str:
    # Three- and five-fold repetition
    rep_count = Counter(board.history)[board.zobrist_hash]
    if rep_count >= 5:
        return "draw by 5 fold repetition"
    if rep_count >= 3:
        return "draw by 3 fold repetition"

    # Fifty-move rule
    if is_draw_by_50(board):
        return "draw by 50 moves"

    # Insufficient material
    if is_draw_by_insufficient_material(board):
        return "draw by insufficient material"

    # Terminal conditions
    if is_checkmate(board, color):
        return "checkmate"
    if is_stalemate(board, color):
        return "stalemate"

    return "ongoing"
