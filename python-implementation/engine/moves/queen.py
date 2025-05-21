from board import Board
from typing import List
from offsets import QUEEN_OFFSETS

from .move import Move
from .helpers import check_bounds


def queen_moves(board: Board, color: str) -> List[Move]:
    """
    Generate all queen slides for the given color.
    Returns a list of Move objects.
    """
    moves = []

    if color == "white":
        queen_char = "Q"
    else:
        queen_char = "q"

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] != queen_char:
                continue
            from_sq = (file, rank)
            for move_f, move_r in QUEEN_OFFSETS:
                target_file = file + move_f
                target_rank = rank + move_r

                while check_bounds(target_file, target_rank):
                    to_sq = (target_file, target_rank)
                    target_square = board[target_file, target_rank]
                    if target_square == board.EMPTY:
                        moves.append(Move(from_sq, to_sq))
                    else:
                        if target_square.isupper() != queen_char.isupper():
                            moves.append(Move(from_sq, to_sq))
                        break

                    target_file += move_f
                    target_rank += move_r

    return moves
