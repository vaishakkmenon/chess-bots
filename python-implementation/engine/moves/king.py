from board import Board
from offsets import KING_OFFSETS
from .helpers import check_bounds

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
        king_char = "K"
    else:
        king_char = "k"

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] == king_char:
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

    return moves
