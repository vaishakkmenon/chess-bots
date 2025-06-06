from typing import List, Union, Tuple
import engine.bitboard.config as config
from engine.bitboard.move import Move
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
) -> List[Union[Move, Tuple[int, int, bool, None, bool, bool]]]:

    moves: List[Union[Move, Tuple[int, int, bool, None, bool, bool]]] = []
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
            if config.USE_RAW_MOVES:
                moves.append((src, dst, is_capture, None, False, False))
            else:
                moves.append(Move(src, dst, capture=is_capture))
            legal_temp &= legal_temp - 1
        tmp &= tmp - 1
    return moves


# Ray based rook move generation
# def generate_rook_moves(
#     rook_bb: int, my_occ: int, their_occ: int
# ) -> List[Move]:
#     """
#     Generate all legal rook moves
#     (including captures) for the given bitboard.
#     """
#     moves: List[Move] = []

#     tmp_rooks = rook_bb
#     while tmp_rooks:
#         src = pop_lsb(tmp_rooks)

#         # For each orthogonal direction
#         for offset in ROOK_OFFSETS:
#             # Determine file shift per step:
#             #   +1 for north moves, -1 for south
#             file_delta = offset
#             if offset == 8 or offset == -8:
#                 file_delta = 0

#             cur = src
#             while True:
#                 prev_file = cur & 7
#                 # break if horizontal wrap
#                 if (file_delta == 1 and prev_file == 7) or (
#                     file_delta == -1 and prev_file == 0
#                 ):
#                     break

#                 tgt = cur + offset
#                 # break if off-board
#                 if tgt < 0 or tgt >= 64:
#                     break

#                 # 1) Blocked by own piece?
#                 if my_occ & (1 << tgt):
#                     break

#                 # 2) Enemy capture?
#                 if their_occ & (1 << tgt):
#                     moves.append(Move(src, tgt, capture=True))
#                     break

#                 # 3) Quiet move
#                 moves.append(Move(src, tgt))

#                 # advance
#                 cur = tgt

#         tmp_rooks &= tmp_rooks - 1
#     return moves
