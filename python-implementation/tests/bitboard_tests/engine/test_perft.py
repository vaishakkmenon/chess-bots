import pytest

from engine.bitboard.board import Board
from engine.bitboard.generator import generate_legal_moves
from engine.bitboard.constants import WHITE, WHITE_KING, BLACK_KING
from engine.bitboard.perft import perft_count, perft_divide, perft_hashed_root


def make_kings_only_board() -> Board:
    b = Board()
    b.bitboards = [0] * 12
    b.white_occ = b.black_occ = b.all_occ = 0
    b.ep_square = None
    b.castling_rights = 0
    b.side_to_move = WHITE
    b.halfmove_clock = 0
    b.fullmove_number = 1
    b.square_to_piece = [None] * 64
    b.bitboards[WHITE_KING] = 1 << 4
    b.bitboards[BLACK_KING] = 1 << 60
    b.update_occupancies()
    for idx, bb in enumerate(b.bitboards):
        t = bb
        while t:
            lsb = t & -t
            sq = lsb.bit_length() - 1
            b.square_to_piece[sq] = idx
            t ^= lsb
    b._compute_zobrist_from_scratch()
    b.zobrist_history = [b.zobrist_key]
    return b


def test_perft_depth_zero_is_one():
    b = Board()
    assert perft_count(b, 0) == 1


def test_perft_depth_one_equals_legal_moves():
    b = Board()
    moves = generate_legal_moves(b)
    assert perft_count(b, 1) == len(moves)


@pytest.mark.parametrize(
    "depth,expected",
    [(1, 20), (2, 400), (3, 8902), (4, 197281)],
)
def test_perft_start_position(depth, expected):
    b = Board()
    assert perft_count(b, depth) == expected


def test_perft_divide_depth_one_sums_to_perft():
    b = Board()
    total = perft_count(b, 1)
    divide = perft_divide(b, 1)
    assert sum(divide.values()) == total
    assert all(cnt == 1 for cnt in divide.values())
    legal_moves = generate_legal_moves(b)
    assert set(divide.keys()) == set(legal_moves)


def test_perft_divide_consistency_with_depth_two():
    b = Board()
    total2 = perft_count(b, 2)
    divide2 = perft_divide(b, 2)
    assert sum(divide2.values()) == total2
    assert any(cnt > 1 for cnt in divide2.values())


def test_perft_hashed_vs_perft_count():
    b = Board()
    assert perft_count(b, 3) == perft_hashed_root(b, 3)
    assert perft_count(b, 4) == perft_hashed_root(b, 4)


def test_perft_respects_fifty_move_draw():
    b = Board()
    b.halfmove_clock = 100
    assert perft_count(b, 1, respect_draws=True) == 1


def test_perft_respects_repetition():
    b = Board()
    for _ in range(2):
        b.zobrist_history.append(b.zobrist_key)
    assert perft_count(b, 1, respect_draws=True) == 1


def test_perft_respects_insufficient_material():
    b = make_kings_only_board()
    assert perft_count(b, 1, respect_draws=True) == 1
