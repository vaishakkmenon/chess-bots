import pytest

from engine.bitboard.board import Board
from engine.bitboard.generator import generate_legal_moves
from engine.bitboard.perft import perft_count, perft_divide


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
