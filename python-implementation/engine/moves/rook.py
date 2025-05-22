from engine.board import Board
from engine.offsets import ROOK_OFFSETS

from engine.moves.move import Move
from engine.moves.helpers import check_bounds

from typing import List


def rook_moves(board: Board, color: str) -> List[Move]:
    """
    Generate all rook slides for the given color.
    Returns a list of Move objects.
    """
    moves = []

    if color == "white":
        rook_char = "R"
    else:
        rook_char = "r"

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] != rook_char:
                continue
            from_sq = (file, rank)
            for move_f, move_r in ROOK_OFFSETS:
                target_file = file + move_f
                target_rank = rank + move_r

                while check_bounds(target_file, target_rank):
                    to_sq = (target_file, target_rank)
                    target_square = board[target_file, target_rank]
                    if target_square == board.EMPTY:
                        moves.append(Move(from_sq, to_sq))
                    else:
                        if target_square.isupper() != rook_char.isupper():
                            moves.append(Move(from_sq, to_sq))
                        break

                    target_file += move_f
                    target_rank += move_r

    return moves
