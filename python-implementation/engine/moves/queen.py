from board import Board
from offsets import QUEEN_OFFSETS
from .helpers import check_bounds


def queen_moves(
    board: Board, color: str
) -> list[tuple[tuple[int, int], tuple[int, int], str | None]]:
    """
    Generate all queen slides for the given color.
    Returns a list of (from_sq, to_sq, None) triples.
    """
    moves = []

    if color == "white":
        queen_char = "Q"
    else:
        queen_char = "q"

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] == queen_char:
                for moveF, moveR in QUEEN_OFFSETS:
                    targetFile = file + moveF
                    targetRank = rank + moveR
                    target = (targetFile, targetRank)

                    while check_bounds(targetFile, targetRank):
                        target_square = board[targetFile, targetRank]
                        if target_square == board.EMPTY:
                            moves.append(((file, rank), target, None))
                        else:
                            if target_square.isupper() != queen_char.isupper():
                                moves.append(((file, rank), target, None))
                            break

                        targetFile += moveF
                        targetRank += moveR
                        target = (targetFile, targetRank)

    return moves
