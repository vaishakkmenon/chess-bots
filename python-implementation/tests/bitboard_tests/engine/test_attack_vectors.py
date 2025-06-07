# New tests verifying Board.is_square_attacked for all piece types
import pytest
from engine.bitboard.board import Board
from engine.bitboard.constants import (
    WHITE,
    BLACK,
    WHITE_PAWN,
    WHITE_KNIGHT,
    WHITE_BISHOP,
    WHITE_ROOK,
    WHITE_QUEEN,
    WHITE_KING,
    BLACK_PAWN,
    BLACK_KNIGHT,
    BLACK_BISHOP,
    BLACK_ROOK,
    BLACK_QUEEN,
    BLACK_KING,
)

PIECE_INDEX = {
    "P": WHITE_PAWN,
    "N": WHITE_KNIGHT,
    "B": WHITE_BISHOP,
    "R": WHITE_ROOK,
    "Q": WHITE_QUEEN,
    "K": WHITE_KING,
    "p": BLACK_PAWN,
    "n": BLACK_KNIGHT,
    "b": BLACK_BISHOP,
    "r": BLACK_ROOK,
    "q": BLACK_QUEEN,
    "k": BLACK_KING,
}


def sq(file: int, rank: int) -> int:
    """Convert 1-indexed file/rank to 0..63 square index."""
    return (rank - 1) * 8 + (file - 1)


def make_board(pieces: dict[int, str]) -> Board:
    board = Board()
    board.bitboards = [0] * 12
    for square, char in pieces.items():
        board.bitboards[PIECE_INDEX[char]] |= 1 << square
    board.update_occupancies()
    return board


ATTACK_TESTS = [
    # Pawn attacks
    ("white pawn e5->d6", {sq(5, 5): "P"}, sq(4, 6), WHITE, True),
    ("white pawn e5->f6", {sq(5, 5): "P"}, sq(6, 6), WHITE, True),
    ("white pawn e5 no->e6", {sq(5, 5): "P"}, sq(5, 6), WHITE, False),
    ("black pawn e4->d3", {sq(5, 4): "p"}, sq(4, 3), BLACK, True),
    ("black pawn e4->f3", {sq(5, 4): "p"}, sq(6, 3), BLACK, True),
    ("black pawn e4 no->e3", {sq(5, 4): "p"}, sq(5, 3), BLACK, False),
    # Knight attacks
    ("white knight e4->g5", {sq(5, 4): "N"}, sq(7, 5), WHITE, True),
    ("white knight e4->f2", {sq(5, 4): "N"}, sq(6, 2), WHITE, True),
    ("white knight e4 no->e5", {sq(5, 4): "N"}, sq(5, 5), WHITE, False),
    ("black knight d5->b6", {sq(4, 5): "n"}, sq(2, 6), BLACK, True),
    ("black knight d5->e7", {sq(4, 5): "n"}, sq(5, 7), BLACK, True),
    ("black knight d5 no->d6", {sq(4, 5): "n"}, sq(4, 6), BLACK, False),
    # Bishop / Queen diagonals
    ("white bishop c1->a3", {sq(3, 1): "B"}, sq(1, 3), WHITE, True),
    ("white bishop f4->b8", {sq(6, 4): "B"}, sq(2, 8), WHITE, True),
    (
        "white bishop blocked by knight",
        {sq(5, 4): "B", sq(7, 6): "N"},
        sq(7, 7),
        WHITE,
        False,
    ),
    ("black queen c8->f5", {sq(3, 8): "q"}, sq(6, 5), BLACK, True),
    (
        "black queen blocked diag",
        {sq(3, 8): "q", sq(5, 6): "p"},
        sq(7, 4),
        BLACK,
        False,
    ),
    # Rook / Queen orthogonals
    ("white rook d4->d7", {sq(4, 4): "R"}, sq(4, 7), WHITE, True),
    ("white rook a1->d1", {sq(1, 1): "R"}, sq(4, 1), WHITE, True),
    (
        "white rook blocked orth",
        {sq(4, 4): "R", sq(4, 6): "P"},
        sq(4, 8),
        WHITE,
        False,
    ),
    ("black queen h8->h5", {sq(8, 8): "q"}, sq(8, 5), BLACK, True),
    (
        "black queen blocked orth",
        {sq(8, 8): "q", sq(8, 6): "P"},
        sq(8, 4),
        BLACK,
        False,
    ),
    # King adjacency
    ("white king e4->d5", {sq(5, 4): "K"}, sq(4, 5), WHITE, True),
    ("white king e4->e3", {sq(5, 4): "K"}, sq(5, 3), WHITE, True),
    ("white king e4 no->g6", {sq(5, 4): "K"}, sq(7, 6), WHITE, False),
    ("black king a8->b8", {sq(1, 8): "k"}, sq(2, 8), BLACK, True),
    ("black king h1->g1", {sq(8, 1): "k"}, sq(7, 1), BLACK, True),
    ("black king h1 no->f1", {sq(8, 1): "k"}, sq(6, 1), BLACK, False),
]


@pytest.mark.parametrize("desc,pieces,target,color,expected", ATTACK_TESTS)
def test_all_attack_vectors(desc, pieces, target, color, expected):
    board = make_board(pieces)
    result = board.is_square_attacked(target, color)
    assert result == expected, f"{desc} expected {expected}, got {result}"


def test_attack_wrong_colour_returns_false():
    board = make_board({sq(4, 4): "R"})
    assert not board.is_square_attacked(sq(4, 7), BLACK)


def test_rook_attack_stops_before_second_enemy():
    board = make_board({sq(4, 4): "R", sq(4, 6): "p", sq(4, 8): "p"})
    assert board.is_square_attacked(sq(4, 6), WHITE)
    assert not board.is_square_attacked(sq(4, 8), WHITE)
