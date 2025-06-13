# tests/test_bishop.py

import pytest
import random

from engine.bitboard.move import Move
from engine.bitboard.utils import expand_occupancy, bit_count, move_to_tuple
from engine.bitboard.magic_constants import RELEVANT_BISHOP_MASKS
from engine.bitboard.build_magics import compute_bishop_attacks_with_blockers
from engine.bitboard.moves.bishop import generate_bishop_moves, bishop_attacks


# ------------------------------------------------------------------------
# 1) New “unit test” that directly exercises your magic‐lookup function.
#    This does not replace your existing move‐generation tests—it just
#    gives you another layer of safety by checking bishop_attacks one‐to‐one.
# ------------------------------------------------------------------------
@pytest.mark.parametrize("sq", range(64))
def test_bishop_attacks_match_reference(sq):
    """
    For each square, pick a handful of random blocker
    subsets (within its relevant mask)
    and check that bishop_attacks(sq, occ) ==
    compute_bishop_attacks_with_blockers(sq, occ).
    """
    mask = RELEVANT_BISHOP_MASKS[sq]
    N = bit_count(mask)
    table_size = 1 << N

    # Test empty mask and full mask first
    for subset_index in (0, table_size - 1):
        occ = expand_occupancy(subset_index, mask)
        expected = compute_bishop_attacks_with_blockers(sq, occ)
        got = bishop_attacks(sq, occ)
        assert got == expected, (
            f"sq={sq}, subset={subset_index}: expected=0x{expected:016x}, "
            f"got=0x{got:016x}"
        )

    # Now test 5 random subsets
    random.seed(sq)  # seed per‐square for reproducibility
    for _ in range(5):
        subset_index = random.randrange(table_size)
        occ = expand_occupancy(subset_index, mask)
        expected = compute_bishop_attacks_with_blockers(sq, occ)
        got = bishop_attacks(sq, occ)
        assert got == expected, (
            f"sq={sq}, subset={subset_index}: expected=0x{expected:016x}, "
            f"got=0x{got:016x}"
        )


# ------------------------------------------------------------------------
# 2) Your existing move‐generation tests follow unchanged.
#    They will now implicitly be testing
#    the new magic version of `bishop_attacks`.
# ------------------------------------------------------------------------


# Helper to extract destinations and capture flags
def dsts_and_caps(moves):
    return sorted([(m[1], m[2]) for m in moves])


def test_bishop_open_board_from_d4():
    # Bishop on d4 (sq=27), empty board
    src = 27
    bishops_bb = 1 << src
    my_occ = 0
    their_occ = 0

    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    # Expected destinations (13 squares) all non‐captures
    expected_dsts = sorted(
        [
            # NW: c5, b6, a7
            34,
            41,
            48,
            # NE: e5, f6, g7, h8
            36,
            45,
            54,
            63,
            # SW: c3, b2, a1
            18,
            9,
            0,
            # SE: e3, f2, g1
            20,
            13,
            6,
        ]
    )
    got = sorted(m[1] for m in moves)
    assert got == expected_dsts
    assert all(not m[2] for m in moves)


def test_bishop_blocked_by_friend_on_b6():
    # Bishop on d4, our pawn on b6 blocks NW ray
    src = 27
    bishops_bb = 1 << src
    my_occ = 1 << 41  # b6
    their_occ = 0

    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    # NW ray should only include c5 (34), then stop
    assert (34, False) in dsts_and_caps(moves)
    assert all(dst not in (41, 48) for dst, cap in dsts_and_caps(moves))


def test_bishop_capture_enemy_on_f6():
    # Bishop on d4, enemy pawn on f6
    src = 27
    bishops_bb = 1 << src
    my_occ = 0
    their_occ = 1 << 45  # f6

    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    # Along NE: should have quiet e5 (36) then capture f6 (45) and stop
    seq = [m for m in moves if m[0] == src]
    ne_moves = [m for m in seq if m[1] in (36, 45)]
    assert dsts_and_caps(ne_moves) == [(36, False), (45, True)]
    # Should not include g7(54) or h8(63)
    assert all(dst not in (54, 63) for dst, _ in dsts_and_caps(seq))


def test_bishop_multiple_pieces():
    # Two bishops: one at c1 (2), one at f4 (29). Mix of captures.
    bishops_bb = (1 << 2) | (1 << 29)
    # place our pawn at d2(11) to block c1→d2
    # place enemy pawn at e5(36) to be captured by f4
    my_occ = 1 << 11
    their_occ = 1 << 36
    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    assert all(not (m[0] == 2 and m[1] == 11) for m in moves)
    assert move_to_tuple(Move(29, 36, capture=True)) in moves


def test_no_bishops_no_moves():
    assert generate_bishop_moves(0, 0, 0) == []


def test_bishop_from_a1_full_ne_traverse():
    # Bishop on a1 (sq=0) should sweep NE to b2(9), c3(18), ..., h8(63)
    src = 0
    bishops_bb = 1 << src
    moves = generate_bishop_moves(bishops_bb, my_occ=0, their_occ=0)
    expected_dsts = [9, 18, 27, 36, 45, 54, 63]
    got = sorted(m[1] for m in moves)
    assert got == expected_dsts
    assert all(not m[2] for m in moves)


def test_bishop_from_h8_full_sw_traverse():
    # Bishop on h8 (sq=63) should sweep SW to g7(54), f6(45), ..., a1(0)
    src = 63
    bishops_bb = 1 << src
    moves = generate_bishop_moves(bishops_bb, my_occ=0, their_occ=0)
    expected_dsts = [54, 45, 36, 27, 18, 9, 0]
    got = sorted(m[1] for m in moves)
    assert sorted(expected_dsts) == got
    assert all(not m[2] for m in moves)


def test_bishop_adjacent_capture_and_block():
    # Bishop on c1 (sq=2), enemy on b2 (sq=9) and our own on a3 (sq=16)
    bishops_bb = 1 << 2
    my_occ = 1 << 16  # block SW beyond
    their_occ = 1 << 9  # capture SW
    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    cap_moves = [(m[1], m[2]) for m in moves if m[2]]
    assert cap_moves == [(9, True)]
    assert all(m[1] != 16 for m in moves)


def test_bishop_fully_blocked_by_friends():
    # Bishop on d4 (27), our pawns on all 4 diagonals at distance 1
    bishops_bb = 1 << 27
    my_occ = sum(1 << sq for sq in [18, 20, 34, 36])  # c3, e3, c5, e5
    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ=0)
    assert all(m[1] not in (18, 20, 34, 36) for m in moves)
    assert moves == []


def test_bishop_long_ray_with_mixed_blockers():
    # Bishop on e3 (sq=20)
    bishops_bb = 1 << 20
    # friendly at g5 (38) blocks NE after one step; enemy at c1 (2) on SW
    my_occ = 1 << 38
    their_occ = 1 << 2
    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    ne = [m for m in moves if m[0] == 20 and m[1] in (29, 38)]
    assert [(m[1], m[2]) for m in ne] == [(29, False)]
    sw = [(m[1], m[2]) for m in moves if m[0] == 20 and m[1] in (11, 2)]
    assert set(sw) == {(11, False), (2, True)}
