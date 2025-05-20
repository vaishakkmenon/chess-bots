from board import Board
from offsets import KING_OFFSETS
from .helpers import check_bounds, is_square_attacked

# (we’ll integrate attack‐checks and castling in a moment)


def king_moves(
    board: Board, color: str
) -> list[tuple[tuple[int, int], tuple[int, int], str | None]]:
    """
    Generate all king moves for the given color.
    Returns a list of (from_sq, to_sq, None) triples.
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
                for moveF, moveR in KING_OFFSETS:
                    targetFile = file + moveF
                    targetRank = rank + moveR
                    target = (targetFile, targetRank)

                    if check_bounds(targetFile, targetRank):
                        target_square = board[targetFile, targetRank]
                        if target_square == board.EMPTY:
                            moves.append(((file, rank), target, None))
                        elif target_square.isupper() != king_char.isupper():
                            moves.append(((file, rank), target, None))
                # Castling
                if (
                    can_castle_kingside
                    and board[sf + 1, sr] == board.EMPTY
                    and board[sf + 2, sr] == board.EMPTY
                    and board[sf + 3, sr] == rook_char
                    and not is_square_attacked(board, (sf, sr), enemy)
                    and not is_square_attacked(board, (sf + 1, sr), enemy)
                    and not is_square_attacked(board, (sf + 2, sr), enemy)
                ):
                    moves.append(
                        (
                            (sf, sr),
                            (sf + 2, sr),
                            None,
                        )
                    )

                if (
                    can_castle_queenside
                    and board[sf - 1, sr] == board.EMPTY
                    and board[sf - 2, sr] == board.EMPTY
                    and board[sf - 3, sr] == board.EMPTY
                    and board[sf - 4, sr] == rook_char
                    and not is_square_attacked(board, (sf, sr), enemy)
                    and not is_square_attacked(board, (sf - 1, sr), enemy)
                    and not is_square_attacked(board, (sf - 2, sr), enemy)
                ):
                    moves.append(
                        (
                            (sf, sr),
                            (sf - 2, sr),
                            None,
                        )
                    )
    return moves
