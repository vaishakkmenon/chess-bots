from typing import List, Union, Tuple
import engine.bitboard.config as config
from engine.bitboard.move import Move
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import MASK_64
from engine.bitboard.bishop_attack_table import BISHOP_ATTACK_TABLE
from engine.bitboard.magic_constants import (
    RELEVANT_BISHOP_MASKS,
    BISHOP_MAGICS,
    BISHOP_SHIFTS,
)

# from engine.bitboard.constants import BISHOP_OFFSETS


def bishop_attacks(sq: int, all_occ: int) -> int:
    """
    Given a square index (0-63) and full occupancy
    return the precomputed bishop mask.
    """
    mask = RELEVANT_BISHOP_MASKS[sq]
    magic = BISHOP_MAGICS[sq]
    shift = BISHOP_SHIFTS[sq]

    masked_occ = all_occ & mask
    idx = ((masked_occ * magic) & MASK_64) >> shift
    return BISHOP_ATTACK_TABLE[sq][idx]


def generate_bishop_moves(
    bishop_bb: int, my_occ: int, their_occ: int
) -> List[Union[Move, Tuple[int, int, bool, None, bool, bool]]]:
    """
    Given a bitboard of all bishops for side-to-move,
    plus my_occ and their_occ,
    return Move objects for all legal bishop moves.
    """
    moves: List[Union[Move, Tuple[int, int, bool, None, bool, bool]]] = []
    full_occ = my_occ | their_occ
    temp = bishop_bb

    while temp:
        src = pop_lsb(temp)
        temp &= temp - 1

        attacks = bishop_attacks(src, full_occ)
        legal = attacks & ~my_occ

        legal_temp = legal
        while legal_temp:
            dst = pop_lsb(legal_temp)
            legal_temp &= legal_temp - 1
            is_capture = bool(their_occ & (1 << dst))
            if config.USE_RAW_MOVES:
                moves.append((src, dst, is_capture, None, False, False))
            else:
                moves.append(Move(src, dst, capture=is_capture))
    return moves


# Ray based bishop move generation
# def generate_bishop_moves(
#     bishops_bb: int, my_occ: int, their_occ: int
# ) -> List[Move]:
#     """
#     Generate all legal bishop moves
#     (including captures) for the given bitboard.
#     """
#     moves: List[Move] = []

#     tmp_bishops = bishops_bb
#     while tmp_bishops:
#         src = pop_lsb(tmp_bishops)

#         # For each diagonal direction
#         for offset in BISHOP_OFFSETS:
#             # Determine file shift per step:
#             #   +1 for east moves, -1 for west
#             file_delta = 1 if offset in (9, -7) else -1

#             cur = src
#             while True:
#                 prev_file = cur & 7
#                 if (prev_file == 7 and file_delta == 1) or (
#                     prev_file == 0 and file_delta == -1
#                 ):
#                     break

#                 tgt = cur + offset
#                 if tgt < 0 or tgt >= 64:
#                     break

#                 # 1) Blocked by our own piece?
#                 if my_occ & (1 << tgt):
#                     break

#                 # 2) Enemy capture?
#                 if their_occ & (1 << tgt):
#                     moves.append(Move(src, tgt, capture=True))
#                     break

#                 # 3) Quiet move
#                 moves.append(Move(src, tgt))

#                 # advance to next square
#                 cur = tgt

#         tmp_bishops &= tmp_bishops - 1
#     return moves
