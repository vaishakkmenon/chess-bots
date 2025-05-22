from engine.board import Board
from engine.offsets import KING_OFFSETS

from engine.moves.move import Move
from engine.moves.helpers import check_bounds, is_square_attacked

from typing import List

# (we’ll integrate attack‐checks and castling in a moment)


def king_moves(board: Board, color: str) -> List[Move]:
    """
    Generate all king moves for the given color.
    Returns a list of Move objects.
    """
    moves = []

    if color == "white":
        enemy = "black"
        king_char = "K"
        rook_char = "R"
        can_castle_kingside = board.white_can_castle_kingside
        can_castle_queenside = board.white_can_castle_queenside
    else:
        enemy = "white"
        king_char = "k"
        rook_char = "r"
        can_castle_kingside = board.black_can_castle_kingside
        can_castle_queenside = board.black_can_castle_queenside

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] == king_char:
                # sf = start_file, sr = start_rank
                sf, sr = file, rank
                from_sq = (file, rank)
                for move_f, move_r in KING_OFFSETS:
                    target_file = file + move_f
                    target_rank = rank + move_r
                    to_sq = (target_file, target_rank)

                    if check_bounds(target_file, target_rank):
                        target_square = board[target_file, target_rank]
                        if (
                            target_square == board.EMPTY
                            or target_square.isupper() != king_char.isupper()
                        ):
                            moves.append(Move(from_sq, to_sq))
                # Castling
                if (
                    can_castle_kingside
                    and (sf, sr) == (5, 1 if color == "white" else 8)
                    and board[sf + 1, sr] == board.EMPTY
                    and board[sf + 2, sr] == board.EMPTY
                    and board[sf + 3, sr] == rook_char
                    and not is_square_attacked(board, (sf, sr), enemy)
                    and not is_square_attacked(board, (sf + 1, sr), enemy)
                    and not is_square_attacked(board, (sf + 2, sr), enemy)
                ):
                    to_sq = (sf + 2, sr)
                    moves.append(Move(from_sq, to_sq, is_castle=True))

                if (
                    can_castle_queenside
                    and (sf, sr) == (5, 1 if color == "white" else 8)
                    and board[sf - 1, sr] == board.EMPTY
                    and board[sf - 2, sr] == board.EMPTY
                    and board[sf - 3, sr] == board.EMPTY
                    and board[sf - 4, sr] == rook_char
                    and not is_square_attacked(board, (sf, sr), enemy)
                    and not is_square_attacked(board, (sf - 1, sr), enemy)
                    and not is_square_attacked(board, (sf - 2, sr), enemy)
                ):
                    to_sq = (sf - 2, sr)
                    moves.append(Move(from_sq, to_sq, is_castle=True))
    return moves
