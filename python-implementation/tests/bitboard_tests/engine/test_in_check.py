from engine.bitboard.board import Board
from engine.bitboard.constants import (
    WHITE,
    BLACK,
    WHITE_KING,
    BLACK_KING,
    BLACK_QUEEN,
    WHITE_QUEEN,
)

PIECE_INDEX = {
    "K": WHITE_KING,
    "k": BLACK_KING,
    "q": BLACK_QUEEN,
    "Q": WHITE_QUEEN,
}


def sq(file: int, rank: int) -> int:
    return (rank - 1) * 8 + (file - 1)


def make_board(pieces: dict[int, str]) -> Board:
    board = Board()
    board.bitboards = [0] * 12
    for square, char in pieces.items():
        board.bitboards[PIECE_INDEX[char]] |= 1 << square
    board.update_occupancies()
    return board


def test_white_in_check() -> None:
    board = make_board({sq(5, 1): "K", sq(5, 8): "q"})
    assert board.in_check(WHITE)


def test_black_not_in_check() -> None:
    board = make_board({sq(5, 8): "k"})
    assert not board.in_check(BLACK)


def test_black_in_check_from_white_queen() -> None:
    board = make_board({sq(5, 8): "k", sq(5, 1): "Q"})
    assert board.in_check(BLACK)


def test_missing_king_returns_false() -> None:
    board = make_board({})
    assert not board.in_check(WHITE)
