from engine.bitboard.board import Board
from engine.bitboard.utils import bit_count
from engine.bitboard.constants import WHITE_KING
from engine.bitboard.moves.king import KING_ATTACKS, generate_king_moves


def test_popcounts():
    assert bit_count(KING_ATTACKS[27]) == 8  # d4
    assert bit_count(KING_ATTACKS[0]) == 3  # a1
    assert bit_count(KING_ATTACKS[63]) == 3  # h8


def test_reasonable_range():
    for mask in KING_ATTACKS:
        pc = bit_count(mask)
        assert 3 <= pc <= 8


def test_king_moves_open_board():
    board = Board()
    board.bitboards = [0] * 12
    board.bitboards[WHITE_KING] = 1 << 27  # King on d4
    board.white_occ = board.bitboards[WHITE_KING]
    board.black_occ = board.all_occ = 0
    moves = generate_king_moves(
        board.bitboards[WHITE_KING], board.white_occ, board.black_occ
    )
    assert len(moves) == 8
