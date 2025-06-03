# tests/bitboard_tests/test_queen.py

import pytest
import random

from engine.bitboard.utils import expand_occupancy, bit_count
from engine.bitboard.moves.queen import generate_queen_moves, queen_attacks
from engine.bitboard.build_magics import (
    compute_rook_attacks_with_blockers,
    compute_bishop_attacks_with_blockers,
)
from engine.bitboard.magic_constants import (
    RELEVANT_ROOK_MASKS,
    RELEVANT_BISHOP_MASKS,
)


# ──────────────────────────────────────────────────────────────────────────────
# 1) “Unit test” comparing the queen’s magic lookup to the slow reference.
#    A queen’s attack is simply rook_ref | bishop_ref.
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("sq", range(64))
def test_queen_attacks_match_reference(sq):
    """
    For each square 0–63, pick a handful of blocker subsets (within the union
    of rook/bishop relevant masks) and confirm that
      queen_attacks(sq, occ)
    matches
      compute_rook_attacks_with_blockers(sq, occ) | compute_bishop_attacks_with_blockers(sq, occ).
    """  # noqa:E501
    # Build combined relevant mask
    mask_r = RELEVANT_ROOK_MASKS[sq]
    mask_b = RELEVANT_BISHOP_MASKS[sq]
    combined_mask = mask_r | mask_b

    N = bit_count(combined_mask)
    table_size = 1 << N

    # For testing, we only consider subsets within combined_mask
    # use expand_occupancy on combined_mask.
    # 1a) Empty‐mask case
    occ = 0
    expected = compute_rook_attacks_with_blockers(
        sq, occ
    ) | compute_bishop_attacks_with_blockers(sq, occ)
    got = queen_attacks(sq, occ)
    assert (
        got == expected
    ), f"sq={sq}, empty‐mask: expected=0x{expected:016x}, got=0x{got:016x}"

    # 1b) Full‐mask case
    occ = combined_mask
    expected = compute_rook_attacks_with_blockers(
        sq, occ
    ) | compute_bishop_attacks_with_blockers(sq, occ)
    got = queen_attacks(sq, occ)
    assert (
        got == expected
    ), f"sq={sq}, full‐mask: expected=0x{expected:016x}, got=0x{got:016x}"

    # 1c) Random subsets
    random.seed(sq)
    for _ in range(5):
        subset_index = random.randrange(table_size)
        occ = expand_occupancy(subset_index, combined_mask)
        expected = compute_rook_attacks_with_blockers(
            sq, occ
        ) | compute_bishop_attacks_with_blockers(sq, occ)
        got = queen_attacks(sq, occ)
        assert (
            got == expected
        ), f"sq={sq}, subset={subset_index}: expected=0x{expected:016x}, got=0x{got:016x}"  # noqa: E501


# ──────────────────────────────────────────────────────────────────────────────
# 2) Move‐generation tests for generate_queen_moves(...)
#    (We only check that specific expected destinations appear,
#     not exact set equality, since Order is not guaranteed.)
# ──────────────────────────────────────────────────────────────────────────────
def dsts_and_caps(moves):
    return sorted((m.dst, m.capture) for m in moves)


def test_queen_open_board_from_d4():
    # Queen on d4 (sq=27), empty board
    src = 27
    queen_bb = 1 << src
    my_occ = 0
    their_occ = 0

    moves = generate_queen_moves(queen_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)  # now we will use dst_caps

    # Rook‐style moves from d4: 14 squares
    rook_expected = {35, 43, 51, 59, 19, 11, 3, 26, 25, 24, 28, 29, 30, 31}
    # Bishop‐style moves from d4: 13 squares
    bishop_expected = {34, 41, 48, 36, 45, 54, 63, 18, 9, 0, 20, 13, 6}

    all_expected = rook_expected | bishop_expected

    # Extract just the destination squares from dst_caps
    got_dsts = {dst for (dst, capture) in dst_caps}

    # Queen’s open‐board move count should be 27
    assert len(moves) == 27
    # Ensure every expected destination is present
    assert all_expected.issubset(got_dsts)


def test_queen_blocked_by_friend_on_d6():
    # Queen on d4 (27), friend on d6 (43) blocks up,
    # friend on b6 (41) blocks NW,
    # friend on f4 (29) blocks right.
    src = 27
    queen_bb = 1 << src
    my_occ = (1 << 43) | (1 << 41) | (1 << 29)
    their_occ = 0

    moves = generate_queen_moves(queen_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)

    # Up‐ray: only d5 (35) should appear, not d6(43) or d7(51) or d8(59)
    assert (35, False) in dst_caps
    assert all(dst not in (43, 51, 59) for dst, cap in dst_caps)

    # NW‐ray: only c5(34) should appear, not b6(41) or a7(48)
    assert (34, False) in dst_caps
    assert all(dst not in (41, 48) for dst, cap in dst_caps)

    # Right‐ray: only e4(28) should appear, not f4(29) etc.
    assert (28, False) in dst_caps
    assert all(dst not in (29, 30, 31) for dst, cap in dst_caps)


def test_queen_capture_enemy_on_f6_and_b4():
    # Queen on d4 (27), enemy at f6 (45) on NE, enemy at b4 (25) on left.
    src = 27
    queen_bb = 1 << src
    my_occ = 0
    their_occ = (1 << 45) | (1 << 25)

    moves = generate_queen_moves(queen_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)

    # NE‐ray: expect e5(36) quiet, then f6(45) capture, stop
    assert (36, False) in dst_caps
    assert (45, True) in dst_caps
    assert all(dst not in (54, 63) for dst, cap in dst_caps)

    # Left‐ray: expect c4(26) quiet, then b4(25) capture, stop
    assert (26, False) in dst_caps
    assert (25, True) in dst_caps
    assert all(dst not in (24,) for dst, cap in dst_caps)  # a4(24) blocked


def test_queen_multiple_queens_and_mixed():
    # Two queens: one at a1(0), one at h8(63)
    queens_bb = (1 << 0) | (1 << 63)
    # Block a1’s upward ray at a4(24), enemy at h4(31) for h8 downward
    my_occ = 1 << 24
    their_occ = 1 << 31

    moves = generate_queen_moves(queens_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)

    # a1’s upward ray: a2(8), a3(16) should appear, but not a4(24)
    assert (8, False) in dst_caps
    assert (16, False) in dst_caps
    assert all(dst not in (24,) for dst, cap in dst_caps)

    # a1’s right ray: b1(1), c1(2), … h1(7)
    for dst in range(1, 8):
        assert (dst, False) in dst_caps

    # h8’s downward ray: h7(55), h6(47), h5(39), then capture h4(31)
    for tgt, cap_flag in [(55, False), (47, False), (39, False), (31, True)]:
        assert (tgt, cap_flag) in dst_caps


def test_no_queens_no_moves():
    assert generate_queen_moves(0, 0, 0) == []


def test_queen_from_a1_full_traverse():
    # Queen on a1 (sq=0) should sweep rank, file, and diagonal from corner:
    # Files: a2(8), a3(16), …, a8(56)
    # Ranks: b1(1), c1(2), …, h1(7)
    # Diagonal NE: b2(9), c3(18), …, h8(63)
    src = 0
    queen_bb = 1 << src
    moves = generate_queen_moves(queen_bb, my_occ=0, their_occ=0)
    dsts = set(m.dst for m in moves)

    expected = set(
        [
            8,
            16,
            24,
            32,
            40,
            48,
            56,  # a‐file
            1,
            2,
            3,
            4,
            5,
            6,
            7,  # 1st rank
            9,
            18,
            27,
            36,
            45,
            54,
            63,
        ]  # NE diagonal
    )
    assert expected.issubset(dsts)


def test_queen_adjacent_capture_and_block():
    # Queen on c3 (sq=18), friend on c4(26) blocks north,
    # enemy on b2(9) on SW diagonal.
    #
    # South‐file (c2=10, c1=2) is open because we only blocked c4.
    queens_bb = 1 << 18
    my_occ = 1 << 26  # block c4 so no c5(34), c6(42), …
    their_occ = 1 << 9  # capture on SW at b2

    moves = generate_queen_moves(queens_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)

    # West ray: queen should move to b3(17) and a3(16)
    assert (17, False) in dst_caps
    assert (16, False) in dst_caps

    # SW diagonal: queen moves to b2(9) as a capture, then stops
    assert (9, True) in dst_caps
    # Nothing beyond b2 on that diagonal—so a1 (0) should NOT appear
    assert all(dst != 0 for dst, cap in dst_caps)

    # South file: c2 (10) and c1 (2) are unblocked,
    # so should appear as quiet moves
    assert (10, False) in dst_caps
    assert (2, False) in dst_caps

    # North is blocked at c4, so no c4 (26), c5, etc.
    assert all(dst not in (26, 34, 42) for dst, cap in dst_caps)


def test_queen_long_ray_with_mixed_blockers():
    # Queen on e3 (sq=20)
    queens_bb = 1 << 20
    # friendly at g5(38) blocks NE after one step; enemy at c1(2) on SW;
    # enemy at e8(60) on file, friend at e2(12) on file below.
    my_occ = (1 << 38) | (1 << 12)
    their_occ = (1 << 2) | (1 << 60)

    moves = generate_queen_moves(queens_bb, my_occ, their_occ)
    dst_caps = dsts_and_caps(moves)

    # NE: e3→f4(29) quiet, then g5(38) friend stops ⇒ only (29, False)
    assert (29, False) in dst_caps
    assert all(dst not in (38, 45, 54, 63) for dst, cap in dst_caps)

    # SW: e3→d2(11) quiet, then c1(2) capture
    sw = [(m.dst, m.capture) for m in moves if m.dst in (11, 2)]
    assert set(sw) == {(11, False), (2, True)}

    # Up file: e3→e4(28), e5(36), e6(44), e7(52), then capture e8(60)
    file_up = [
        (m.dst, m.capture) for m in moves if m.dst in (28, 36, 44, 52, 60)
    ]
    assert (60, True) in file_up
    # Ensure no e2(12) or e1(4) (blocked by friend at e2)
    assert all(dst not in (12, 4) for dst, cap in dst_caps)
