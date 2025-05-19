from board import Board
from offsets import ROOK_OFFSETS
from .helpers import check_bounds


def rook_moves(
    board: Board, color: str
) -> list[tuple[tuple[int, int], tuple[int, int], str | None]]:
    """
    Generate all rook slides for the given color.
    Returns a list of (from_sq, to_sq, None) triples.
    """
    moves = []

    if color == "white":
        rook_char = "R"
    else:
        rook_char = "r"

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] == rook_char:
                for moveF, moveR in ROOK_OFFSETS:
                    targetFile = file + moveF
                    targetRank = rank + moveR
                    target = (targetFile, targetRank)

                    while check_bounds(targetFile, targetRank):
                        target_square = board[targetFile, targetRank]
                        if target_square == board.EMPTY:
                            moves.append(((file, rank), target, None))
                        else:
                            if target_square.isupper() != rook_char.isupper():
                                moves.append(((file, rank), target, None))
                            break

                        targetFile += moveF
                        targetRank += moveR
                        target = (targetFile, targetRank)

    return moves
