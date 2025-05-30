from engine.bitboard.move import Move
from engine.bitboard.utils import bit_count
from engine.bitboard.moves.knight import (
    KNIGHT_ATTACKS,
    knight_attacks,
    generate_knight_moves,
)


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
        moves = generate_knight_moves(
            1 << sq,
            0,
            0,
        )
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
    moves = generate_knight_moves(1 << sq, 0, 0)
    assert moves == [Move(sq, i) for i in expected_indices]


def test_generate_knight_moves_capture_flag():
    # Setup a knight on e4 (28), with enemies on two of its attack squares
    sq = 28
    bb_knight = 1 << sq
    my_occ = 0
    their_occ = (1 << 45) | (1 << 38)  # enemies on g5(38) and f6(45)

    moves = generate_knight_moves(bb_knight, my_occ, their_occ)

    # Extract capture moves
    cap_moves = [m for m in moves if m.capture]

    # Check that the destinations match, regardless of order
    cap_dsts = sorted(m.dst for m in cap_moves)
    expected_dsts = sorted([38, 45])
    assert cap_dsts == expected_dsts

    # And verify their capture flag is True
    assert all(m.capture for m in cap_moves)

    # Check non-capture moves are present with capture=False
    non_caps = [m for m in moves if not m.capture]
    assert all(not m.capture for m in non_caps)
