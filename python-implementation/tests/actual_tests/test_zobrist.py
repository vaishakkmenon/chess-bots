# tests/test_zobrist_hash.py

import pytest
from engine.board import Board
from engine.zobrist import (
    Zobrist,
    PIECE_ORDER,
    CASTLING_RIGHTS,
    EN_PASSANT_FILES,
)

MAX_64BIT = 2**64 - 1


@pytest.fixture(scope="module")
def zobrist():
    return Zobrist()


def test_compute_hash_consistency(zobrist):
    board = Board()
    board.init_positions()

    # Compute hash for white to move
    hash_white_1 = zobrist.compute_hash(board, "white")
    hash_white_2 = zobrist.compute_hash(board, "white")
    assert (
        hash_white_1 == hash_white_2
    ), "Hashes for same position/side should match"

    # Compute hash for black to move
    hash_black_1 = zobrist.compute_hash(board, "black")
    hash_black_2 = zobrist.compute_hash(board, "black")
    assert (
        hash_black_1 == hash_black_2
    ), "Hashes for same position/side should match"

    # Hashes for white and black to move should differ
    assert (
        hash_white_1 != hash_black_1
    ), "Hashes for different side to move should differ"


def test_piece_square_table_size(zobrist):
    assert len(zobrist.piece_square) == len(
        PIECE_ORDER
    ), "Should have 12 piece types"
    for piece_row in zobrist.piece_square:
        assert len(piece_row) == 64, "Each piece must have 64 squares"


def test_castling_rights_table_size(zobrist):
    assert set(zobrist.castling_rights.keys()) == set(
        CASTLING_RIGHTS
    ), "Castling rights keys mismatch"
    for val in zobrist.castling_rights.values():
        assert isinstance(val, int), "Castling rights values must be int"
        assert 0 <= val <= MAX_64BIT, "Castling rights values out of range"


def test_en_passant_table_size(zobrist):
    assert set(zobrist.en_passant.keys()) == set(
        EN_PASSANT_FILES
    ), "En passant keys mismatch"
    for val in zobrist.en_passant.values():
        assert isinstance(val, int), "En passant values must be int"
        assert 0 <= val <= MAX_64BIT, "En passant values out of range"


def test_side_to_move_value(zobrist):
    val = zobrist.side_to_move
    assert isinstance(val, int), "Side to move must be int"
    assert 0 <= val <= MAX_64BIT, "Side to move value out of range"


def test_reproducibility():
    # Create two instances and verify values match exactly due to fixed seed
    z1 = Zobrist()
    z2 = Zobrist()

    # Test piece-square table equality
    for p in range(len(PIECE_ORDER)):
        for sq in range(64):
            assert (
                z1.piece_square[p][sq] == z2.piece_square[p][sq]
            ), "Piece-square values differ"

    # Test castling rights equality
    for key in CASTLING_RIGHTS:
        assert (
            z1.castling_rights[key] == z2.castling_rights[key]
        ), "Castling rights values differ"

    # Test en passant equality
    for file in EN_PASSANT_FILES:
        assert (
            z1.en_passant[file] == z2.en_passant[file]
        ), "En passant values differ"

    # Test side to move equality
    assert z1.side_to_move == z2.side_to_move, "Side to move values differ"
