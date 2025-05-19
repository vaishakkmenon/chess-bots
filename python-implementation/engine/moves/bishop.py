from board import Board
from offsets import BISHOP_OFFSETS
from .helpers import check_bounds


def bishop_moves(
    board: Board, color: str
) -> list[tuple[tuple[int, int], tuple[int, int], str | None]]:
    """
    Generate all bishop slides for the given color.
    Returns a list of (from_sq, to_sq, None) triples.
    """
    moves = []

    if color == "white":
        bishop_char = "B"
    else:
        bishop_char = "b"

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] == bishop_char:
                for moveF, moveR in BISHOP_OFFSETS:
                    targetFile = file + moveF
                    targetRank = rank + moveR
                    target = (targetFile, targetRank)

                    while check_bounds(targetFile, targetRank):
                        target_square = board[targetFile, targetRank]
                        if target_square == board.EMPTY:
                            moves.append(((file, rank), target, None))
                        else:
                            if (
                                target_square.isupper()
                                != bishop_char.isupper()
                            ):
                                moves.append(((file, rank), target, None))
                            break

                        targetFile += moveF
                        targetRank += moveR
                        target = (targetFile, targetRank)

    return moves
