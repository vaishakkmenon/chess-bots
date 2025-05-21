from board import Board
from offsets import KNIGHT_OFFSETS
from .move import Move
from .helpers import check_bounds


def knight_moves(board: Board, color: str) -> list[Move]:
    """
    Generate all knight jumps for the given color.
    Returns a list of Move objects.
    """
    moves = []
    if color == "white":
        knight_char = "N"
    else:
        knight_char = "n"

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] != knight_char:
                continue

            from_sq = (file, rank)
            for move_f, move_r in KNIGHT_OFFSETS:

                target_file = file + move_f
                target_rank = rank + move_r
                to_sq = (target_file, target_rank)

                if not check_bounds(*to_sq):
                    continue

                target_square = board[target_file, target_rank]

                if (
                    target_square == board.EMPTY
                    or target_square.isupper() != knight_char.isupper()
                ):
                    moves.append(Move(from_sq, to_sq))
    return moves
