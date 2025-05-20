from board import Board
from offsets import KNIGHT_OFFSETS
from .helpers import check_bounds


def knight_moves(
    board: Board, color: str
) -> list[tuple[tuple[int, int], tuple[int, int], str | None]]:
    """
    Generate all knight jumps for the given color.
    Returns a list of (from_sq, to_sq, None) triples.
    """
    moves = []
    if color == "white":
        knight_char = "N"
    else:
        knight_char = "n"

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] == knight_char:
                for moveF, moveR in KNIGHT_OFFSETS:

                    target = targetFile, targetRank = (
                        file + moveF,
                        rank + moveR,
                    )

                    if not check_bounds(targetFile, targetRank):
                        continue

                    targetSquare = board[targetFile, targetRank]

                    if (
                        targetSquare == board.EMPTY
                        or targetSquare.isupper() != knight_char.isupper()
                    ):
                        moves.append(((file, rank), target, None))
    return moves
