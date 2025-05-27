import pytest
from engine.bitboard.board import Board
from engine.bitboard.constants import INITIAL_MASKS

# from engine.bitboard.constants import (
#     WHITE_PAWN,
#     WHITE_KNIGHT,
#     WHITE_BISHOP,
#     WHITE_ROOK,
#     WHITE_QUEEN,
#     WHITE_KING,
#     BLACK_PAWN,
#     BLACK_KNIGHT,
#     BLACK_BISHOP,
#     BLACK_ROOK,
#     BLACK_QUEEN,
#     BLACK_KING,
# )


@pytest.fixture
def board():
    return Board()


def test_initial_bitboards(board):
    # Verify each bitboard matches the static INITIAL_MASKS
    for idx, expected in enumerate(INITIAL_MASKS):
        assert (
            board.bitboards[idx] == expected
        ), f"bitboards[{idx}] mismatch: got {hex(board.bitboards[idx])}, expected {hex(expected)}"  # noqa: E501
