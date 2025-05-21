from board import Board
from moves.helpers import is_square_attacked


def in_check(board: Board, color: str) -> bool:
    king_char = "K" if color == "white" else "k"
    enemy = "black" if color == "white" else "white"

    for file in range(1, 9):
        for rank in range(1, 9):
            if board[file, rank] == king_char:
                return is_square_attacked(board, (file, rank), enemy)

    raise ValueError(f"No {color} king found on board")
