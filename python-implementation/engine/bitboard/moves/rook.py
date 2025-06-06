from typing import List
from engine.bitboard.config import RawMove  # noqa: TC002
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import MASK_64
from engine.bitboard.rook_attack_table import ROOK_ATTACK_TABLE
from engine.bitboard.magic_constants import (
    RELEVANT_ROOK_MASKS,
    ROOK_MAGICS,
    ROOK_SHIFTS,
)

# from engine.bitboard.constants import ROOK_OFFSETS


def rook_attacks(sq: int, all_occ: int) -> int:
    """
    Given a square 0-63 and the full occupancy bitboard,
    return the precomputed rook attack mask via magic lookup.
    """
    mask = RELEVANT_ROOK_MASKS[sq]
    magic = ROOK_MAGICS[sq]
    shift = ROOK_SHIFTS[sq]

    masked_occ = all_occ & mask
    idx = ((masked_occ * magic) & MASK_64) >> shift
    return ROOK_ATTACK_TABLE[sq][idx]


def generate_rook_moves(
    rook_bb: int, my_occ: int, their_occ: int
) -> List[RawMove]:
    """
    Given a bitboard of all rook for side-to-move,
    plus my_occ and their_occ, return RawMove moves for all legal rook moves.
    """
    moves: List[RawMove] = []
    full_occ = my_occ | their_occ
    tmp = rook_bb
    while tmp:
        src = pop_lsb(tmp)
        attacks = rook_attacks(src, full_occ)
        legal = attacks & ~my_occ
        legal_temp = legal
        while legal_temp:
            dst = pop_lsb(legal_temp)
            is_capture = bool(their_occ & (1 << dst))
            moves.append((src, dst, is_capture, None, False, False))
            legal_temp &= legal_temp - 1
        tmp &= tmp - 1
    return moves
