from engine.bitboard.moves.knight import (
    KNIGHT_ATTACKS,
    knight_attacks,
    generate_knight_moves,
)
from engine.bitboard.move import Move
from engine.bitboard.utils import bit_count


# Helper to build expected mask
def mask_from_indices(indices):
    return sum(1 << i for i in indices)


def test_knight_attacks_table():
    # # Print bitboard visually to ensure correct moves
    # from engine.bitboard.utils import print_bitboard
    # sq = 28  # e4
    # bb = knight_attacks(sq)
    # print_bitboard(bb, source_sq=sq)

    # Verify the KNIGHT_ATTACKS table matches expected masks
    # a1 (0): b3(17), c2(10)
    assert KNIGHT_ATTACKS[0] == mask_from_indices([10, 17])
    # h1 (7): f2(13), g3(22)
    assert KNIGHT_ATTACKS[7] == mask_from_indices([13, 22])
    # e4 (28): expected knight moves at indices [11,13,18,22,34,38,43,45]
    expected_center = [11, 13, 18, 22, 34, 38, 43, 45]
    assert KNIGHT_ATTACKS[28] == mask_from_indices(expected_center)


def test_knight_attacks_api():
    # The API function should return the same as the table
    for sq in [0, 7, 28, 36]:
        assert knight_attacks(sq) == KNIGHT_ATTACKS[sq]


def test_generate_knight_moves_counts_and_contents():
    # For various squares, check that generate_knight_moves returns
    # correct count and Move objects
    for sq in [0, 7, 28, 36]:
        bitboard = KNIGHT_ATTACKS[sq]
        moves = generate_knight_moves(sq)
        # Count check
        assert len(moves) == bit_count(bitboard)
        # Content check: each Move.dst corresponds to a set bit
        dsts = sorted(move.dst for move in moves)
        expected = sorted([i for i in range(64) if (bitboard >> i) & 1])
        assert dsts == expected
        # src field check
        assert all(move.src == sq for move in moves)


def test_edge_cases_h8():
    # h8 (63) only moves: g6(46), f7(53)
    sq = 63
    expected_indices = [46, 53]
    assert generate_knight_moves(sq) == [Move(sq, i) for i in expected_indices]
