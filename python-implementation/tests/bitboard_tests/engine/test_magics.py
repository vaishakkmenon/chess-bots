#!/usr/bin/env python3
"""Tests for correctness of saved magic tables."""

import pytest

from engine.bitboard.magic_constants import (
    RELEVANT_ROOK_MASKS,
    ROOK_MAGICS,
    ROOK_SHIFTS,
    RELEVANT_BISHOP_MASKS,
    BISHOP_MAGICS,
    BISHOP_SHIFTS,
)
from engine.bitboard.rook_attack_table import ROOK_ATTACK_TABLE
from engine.bitboard.bishop_attack_table import BISHOP_ATTACK_TABLE
from engine.bitboard.utils import expand_occupancy, bit_count
from engine.bitboard.build_magics import (
    compute_rook_attacks_with_blockers,
    compute_bishop_attacks_with_blockers,
)

MASK64 = 0xFFFF_FFFF_FFFF_FFFF


def verify(piece: str):
    if piece == "rook":
        masks, magics, shifts, tables = (
            RELEVANT_ROOK_MASKS,
            ROOK_MAGICS,
            ROOK_SHIFTS,
            ROOK_ATTACK_TABLE,
        )
        compute = compute_rook_attacks_with_blockers
    else:
        masks, magics, shifts, tables = (
            RELEVANT_BISHOP_MASKS,
            BISHOP_MAGICS,
            BISHOP_SHIFTS,
            BISHOP_ATTACK_TABLE,
        )
        compute = compute_bishop_attacks_with_blockers

    for sq in range(64):
        mask = masks[sq]
        magic = magics[sq]
        shift = shifts[sq]
        table = tables[sq]

        N = bit_count(mask)
        ideal_shift = 64 - N
        assert (
            ideal_shift <= shift <= ideal_shift + 3
        ), f"{piece} sq{sq}: shift outside allowed window"

        table_size = 1 << N
        assert len(table) == table_size, f"{piece} sq{sq}: wrong table len"

        for subset in range(table_size):
            occ = expand_occupancy(subset, mask)
            idx = ((occ * magic) & MASK64) >> shift
            attack_from_table = table[idx]
            attack_ref = compute(sq, occ)
            if attack_from_table != attack_ref:
                raise AssertionError(
                    f"{piece} sq{sq} subset{subset}: "
                    f"table 0x{attack_from_table:016x} "
                    f"!= ref 0x{attack_ref:016x}"
                )
    print(f"All {piece} magics verified.")


@pytest.mark.parametrize("sq", [0, 27, 63])
def test_rook_magic_subset(sq):
    mask = RELEVANT_ROOK_MASKS[sq]
    magic = ROOK_MAGICS[sq]
    shift = ROOK_SHIFTS[sq]
    table = ROOK_ATTACK_TABLE[sq]
    for subset in [0, 1, (1 << bit_count(mask)) - 1]:
        occ = expand_occupancy(subset, mask)
        idx = ((occ * magic) & MASK64) >> shift
        ref = compute_rook_attacks_with_blockers(sq, occ)
        assert table[idx] == ref


@pytest.mark.parametrize("sq", [0, 27, 63])
def test_bishop_magic_subset(sq):
    mask = RELEVANT_BISHOP_MASKS[sq]
    magic = BISHOP_MAGICS[sq]
    shift = BISHOP_SHIFTS[sq]
    table = BISHOP_ATTACK_TABLE[sq]
    for subset in [0, 1, (1 << bit_count(mask)) - 1]:
        occ = expand_occupancy(subset, mask)
        idx = ((occ * magic) & MASK64) >> shift
        ref = compute_bishop_attacks_with_blockers(sq, occ)
        assert table[idx] == ref


def main():
    verify("rook")
    verify("bishop")
    print("✅ All magic tables match reference generators.")


if __name__ == "__main__":
    main()
