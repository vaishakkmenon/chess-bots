# moves/helpers.py

from board import Board
from offsets import (
    PAWN_ATTACK_OFFSETS,
    BISHOP_OFFSETS,
    ROOK_OFFSETS,
    KNIGHT_OFFSETS,
    KING_OFFSETS,
)

# Function used to check bounds
# f = file, r = rank


def check_bounds(f, r):
    return 1 <= f <= 8 and 1 <= r <= 8


def is_square_attacked(
    board: Board, square: tuple[int, int], color: str
) -> bool:
    """
    Return True if `square` is attacked by any piece of the given `color`.
    Debug prints show which attack vector fires or what blocks it.
    """
    sq_file, sq_rank = square

    # Pawn Attacks
    for file, rank in PAWN_ATTACK_OFFSETS[color]:
        test_file, test_rank = sq_file + file, sq_rank + rank
        if not check_bounds(test_file, test_rank):
            continue
        piece = board[test_file, test_rank]
        if piece == ("P" if color == "white" else "p"):
            return True

    # Knight Attacks
    knight_char = "N" if color == "white" else "n"
    for file, rank in KNIGHT_OFFSETS:
        test_file, test_rank = sq_file + file, sq_rank + rank
        if not check_bounds(test_file, test_rank):
            continue
        piece = board[test_file, test_rank]
        if piece == knight_char:
            return True

    # Bishop/Queen diagonal attacks
    diag_chars = ("B", "Q") if color == "white" else ("b", "q")
    for file, rank in BISHOP_OFFSETS:
        test_file, test_rank = sq_file + file, sq_rank + rank
        while check_bounds(test_file, test_rank):
            piece = board[test_file, test_rank]
            if piece != board.EMPTY:
                if piece in diag_chars:
                    return True
                else:
                    break
            test_file += file
            test_rank += rank

    # Rook/Queen orthogonal attacks
    ortho_chars = ("R", "Q") if color == "white" else ("r", "q")
    for file, rank in ROOK_OFFSETS:
        test_file, test_rank = sq_file + file, sq_rank + rank
        while check_bounds(test_file, test_rank):
            piece = board[test_file, test_rank]
            if piece != board.EMPTY:
                if piece in ortho_chars:
                    return True
                else:
                    break
            test_file += file
            test_rank += rank

    # King adjacency
    king_char = "K" if color == "white" else "k"
    for file, rank in KING_OFFSETS:
        test_file, test_rank = sq_file + file, sq_rank + rank
        if not check_bounds(test_file, test_rank):
            continue
        if (test_file, test_rank) == (sq_file, sq_rank):
            continue
        piece = board[test_file, test_rank]
        if piece == king_char:
            return True

    return False
