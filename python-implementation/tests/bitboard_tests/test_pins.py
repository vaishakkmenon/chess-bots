from engine.bitboard.board import Board
from engine.bitboard.constants import (
    WHITE,
    WHITE_KING,
    WHITE_ROOK,
    WHITE_PAWN,
    WHITE_BISHOP,
    WHITE_KNIGHT,
    BLACK_ROOK,
    BLACK_BISHOP,
    BLACK_KNIGHT,
    BLACK_QUEEN,
)
from engine.bitboard.generator import generate_legal_moves

PIECE_INDEX = {
    "K": WHITE_KING,
    "R": WHITE_ROOK,
    "P": WHITE_PAWN,
    "B": WHITE_BISHOP,
    "N": WHITE_KNIGHT,
    "r": BLACK_ROOK,
    "b": BLACK_BISHOP,
    "n": BLACK_KNIGHT,
    "q": BLACK_QUEEN,
}


def sq(file: int, rank: int) -> int:
    return (rank - 1) * 8 + (file - 1)


def make_board(pieces: dict[int, str]) -> Board:
    board = Board()
    board.bitboards = [0] * 12
    for square, char in pieces.items():
        board.bitboards[PIECE_INDEX[char]] |= 1 << square
    board.update_occupancies()
    board.side_to_move = WHITE
    return board


def test_pinned_pieces_only_move_along_pin() -> None:
    board = make_board(
        {
            sq(5, 1): "K",  # e1
            sq(4, 1): "R",  # d1
            sq(6, 1): "R",  # f1
            sq(4, 2): "P",  # d2
            sq(5, 2): "P",  # e2
            sq(6, 2): "P",  # f2
            sq(7, 7): "P",  # g7 promotion pawn
            sq(1, 1): "r",  # a1
            sq(8, 1): "r",  # h1
            sq(3, 3): "b",  # c3
            sq(5, 8): "q",  # e8
            sq(7, 3): "b",  # g3
        }
    )

    moves = generate_legal_moves(board)

    def dst_caps(src: int) -> set[tuple[int, bool]]:
        return {(m[1], m[2]) for m in moves if m[0] == src}

    assert dst_caps(sq(4, 1)) == {(2, False), (1, False), (0, True)}
    assert dst_caps(sq(6, 1)) == {(6, False), (7, True)}
    assert dst_caps(sq(4, 2)) == {(18, True)}
    assert dst_caps(sq(5, 2)) == {(20, False), (28, False)}
    assert dst_caps(sq(6, 2)) == {(22, True)}

    promo_moves = [m for m in moves if m[0] == sq(7, 7)]
    assert len(promo_moves) == 4
    assert all(m[1] == sq(7, 8) for m in promo_moves)


def test_pinned_bishop_moves_along_pin() -> None:
    board = make_board(
        {
            sq(5, 1): "K",  # king e1
            sq(3, 3): "B",  # bishop c3 pinned on diagonal
            sq(1, 5): "b",  # black bishop a5 pinning piece
        }
    )

    moves = [m for m in generate_legal_moves(board) if m[0] == sq(3, 3)]
    targets = {m[1] for m in moves}

    expected = {sq(2, 4), sq(4, 2), sq(1, 5)}
    assert targets == expected


def test_pinned_knight_no_moves() -> None:
    board = make_board({sq(5, 1): "K", sq(5, 2): "N", sq(5, 8): "r"})

    moves = generate_legal_moves(board)
    assert all(m[0] != sq(5, 2) for m in moves)
