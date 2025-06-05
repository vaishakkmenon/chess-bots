from engine.bitboard.board import Board
from engine.bitboard.constants import (
    WHITE,
    WHITE_KING,
    WHITE_ROOK,
    WHITE_PAWN,
    BLACK_ROOK,
    BLACK_BISHOP,
    BLACK_QUEEN,
)
from engine.bitboard.generator import generate_legal_moves

PIECE_INDEX = {
    "K": WHITE_KING,
    "R": WHITE_ROOK,
    "P": WHITE_PAWN,
    "r": BLACK_ROOK,
    "b": BLACK_BISHOP,
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
        return {(m.dst, m.capture) for m in moves if m.src == src}

    assert dst_caps(sq(4, 1)) == {(2, False), (1, False), (0, True)}
    assert dst_caps(sq(6, 1)) == {(6, False), (7, True)}
    assert dst_caps(sq(4, 2)) == {(18, True)}
    assert dst_caps(sq(5, 2)) == {(20, False), (28, False)}
    assert dst_caps(sq(6, 2)) == {(22, True)}

    promo_moves = [m for m in moves if m.src == sq(7, 7)]
    assert len(promo_moves) == 4
    assert all(m.dst == sq(7, 8) for m in promo_moves)
