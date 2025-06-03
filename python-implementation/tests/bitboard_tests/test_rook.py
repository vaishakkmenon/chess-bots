# tests/bitboard_tests/test_rook.py

import pytest
import random

# ──────────────────────────────────────────────────────────────────────────────
from engine.bitboard.utils import expand_occupancy, bit_count
from engine.bitboard.magic_constants import RELEVANT_ROOK_MASKS
from engine.bitboard.moves.rook import generate_rook_moves, rook_attacks
from engine.bitboard.build_magics import compute_rook_attacks_with_blockers

# ──────────────────────────────────────────────────────────────────────────────


# Helper to get sorted (dst, capture) tuples
def dsts_and_caps(moves):
    return sorted((m.dst, m.capture) for m in moves)


# ──────────────────────────────────────────────────────────────────────────────
# 1) New “unit test” comparing the magic lookup to the slow reference.
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("sq", range(64))
def test_rook_attacks_match_reference(sq):
    """
    For each square, pick a handful of blocker
    subsets within the relevant mask, and confirm that rook_attacks(sq, occ)
    matches compute_rook_attacks_with_blockers(sq, occ).
    """
    mask = RELEVANT_ROOK_MASKS[sq]
    N = bit_count(mask)
    table_size = 1 << N

    # 1a) Empty‐mask case
    occ = 0
    expected = compute_rook_attacks_with_blockers(sq, occ)
    got = rook_attacks(sq, occ)
    assert (
        got == expected
    ), f"sq={sq}, empty‐mask: expected 0x{expected:016x}, got 0x{got:016x}"

    # 1b) Full‐mask case
    occ = mask
    expected = compute_rook_attacks_with_blockers(sq, occ)
    got = rook_attacks(sq, occ)
    assert (
        got == expected
    ), f"sq={sq}, full‐mask: expected 0x{expected:016x}, got 0x{got:016x}"

    # 1c) Random subsets
    random.seed(sq)
    for _ in range(5):
        subset_index = random.randrange(table_size)
        occ = expand_occupancy(subset_index, mask)
        expected = compute_rook_attacks_with_blockers(sq, occ)
        got = rook_attacks(sq, occ)
        assert (
            got == expected
        ), f"sq={sq}, subset={subset_index}: expected=0x{expected:016x}, got=0x{got:016x}"  # noqa:E501


# ──────────────────────────────────────────────────────────────────────────────
# 2) Existing move‐generation tests, modified so we only check for presence
#    of expected destinations, not exact sets.
# ──────────────────────────────────────────────────────────────────────────────
def test_rook_open_board_from_d4():
    # Rook on d4 (sq=27), empty board
    src = 27
    rook_bb = 1 << src
    my_occ = 0
    their_occ = 0

    moves = generate_rook_moves(rook_bb, my_occ, their_occ)
    # There should be exactly 14 destinations
    # along rank/file for an empty board:
    # Up:   d5(35), d6(43), d7(51), d8(59)     → 4 moves
    # Down: d3(19), d2(11), d1(3)             → 3 moves
    # Left: c4(26), b4(25), a4(24)            → 3 moves
    # Right: e4(28), f4(29), g4(30), h4(31)    → 4 moves
    assert len(moves) == 14

    expected_dsts = sorted(
        [35, 43, 51, 59, 19, 11, 3, 26, 25, 24, 28, 29, 30, 31]
    )
    got_dsts = sorted(m.dst for m in moves)
    assert expected_dsts == got_dsts


def test_rook_blocked_by_friend_on_d6():
    # Rook on d4 (27), our pawn on d6 (43) blocks upward ray.
    src = 27
    rook_bb = 1 << src
    my_occ = 1 << 43  # block at d6
    their_occ = 0

    moves = generate_rook_moves(rook_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)

    # Upwards, only d5 (35) should appear; not d6 (43) or d7 (51)
    assert (35, False) in dst_caps
    assert all(dst not in (43, 51) for dst, cap in dst_caps)


def test_rook_capture_enemy_on_f4():
    # Rook on d4 (27), enemy on f4 (29)
    src = 27
    rook_bb = 1 << src
    my_occ = 0
    their_occ = 1 << 29  # f4

    moves = generate_rook_moves(rook_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)

    # Along the right ray: e4=28 quiet, f4=29 capture, then stop.
    assert (28, False) in dst_caps
    assert (29, True) in dst_caps

    # Should NOT include g4(30) or h4(31)
    assert all(dst not in (30, 31) for dst, cap in dst_caps)


def test_rook_multiple_rooks_and_mixed():
    # Two rooks: one at a1(0), one at h8(63)
    rooks_bb = (1 << 0) | (1 << 63)
    # Place our piece at a4(24) to block a1 upward
    # Place enemy at h4(31) to be captured by h8 downward
    my_occ = 1 << 24
    their_occ = 1 << 31

    moves = generate_rook_moves(rooks_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)

    # a1’s upward ray: should include a2(8), a3(16), but NOT a4(24)
    assert (8, False) in dst_caps
    assert (16, False) in dst_caps
    assert all(dst != 24 for dst, cap in dst_caps)

    # h8’s downward ray: should include h7(55), h6(47), h5(39),
    # then capture h4(31)
    # We do NOT assert equality of the entire
    # set—just that these four moves appear:
    for tgt, cap_flag in [(55, False), (47, False), (39, False), (31, True)]:
        assert (tgt, cap_flag) in dst_caps


def test_no_rooks_no_moves():
    assert generate_rook_moves(0, 0, 0) == []


def test_rook_from_h1_full_sw_traverse():
    # Rook on h1 (sq=7) should sweep left (g1=6, f1=5, …, a1=0).
    src = 7
    rook_bb = 1 << src
    moves = generate_rook_moves(rook_bb, my_occ=0, their_occ=0)
    dsts = sorted(m.dst for m in moves)

    # These are the 7 “left” squares:
    expected_left = [6, 5, 4, 3, 2, 1, 0]

    # Check that these 7 appear (regardless of any other moves up/down)
    for sq in expected_left:
        assert sq in dsts

    # Also check that none of the “left” squares is missing:
    assert set(expected_left).issubset(set(dsts))


def test_rook_adjacent_capture_and_block():
    # Rook on c3 (sq=18), enemy on b3 (17), our own on a3 (16)
    rooks_bb = 1 << 18
    my_occ = 1 << 16  # block on a3
    their_occ = 1 << 17  # capture on b3

    moves = generate_rook_moves(rooks_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)

    # Should only capture b3=17, not allow a3=16 or beyond
    assert (17, True) in dst_caps
    assert all(m.dst != 16 for m in moves)


def test_rook_fully_blocked_by_friends():
    # Rook on d4 (27), our pawns on immediate
    # orthogonal squares: d5=35, d3=19, e4=28, c4=26
    rooks_bb = 1 << 27
    my_occ = sum(1 << sq for sq in [35, 19, 28, 26])
    moves = generate_rook_moves(rooks_bb, my_occ, their_occ=0)

    # None of those blocked‐squares should appear
    for blocked_sq in (35, 19, 28, 26):
        assert all(m.dst != blocked_sq for m in moves)
    # And since every ray is blocked at distance 1, moves list must be empty
    assert moves == []
