from board import Board
from .helpers import check_bounds

KNIGHT_OFFSETS = Board.KNIGHT_OFFSETS


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
        # start_rank = 1
    else:
        knight_char = "n"
        # start_rank = 8

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
                        targetSquare != board.EMPTY
                        and targetSquare == board.EMPTY
                        or targetSquare.isupper() != knight_char.isupper()
                    ):
                        moves.append(((file, rank), target, None))
    return moves
