from typing import List
from engine.bitboard.move import Move
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import KNIGHT_OFFSETS

# Precompute knight attack bitboards for all 64 squares
KNIGHT_ATTACKS = [0] * 64
for sq in range(64):
    attacks = 0
    src_mask = 1 << sq
    file = sq & 7
    for offset in KNIGHT_OFFSETS:
        tgt = sq + offset
        if 0 <= tgt < 64:
            df = abs((tgt & 7) - (sq & 7))
            dr = abs((tgt >> 3) - (sq >> 3))
            if (df, dr) in ((1, 2), (2, 1)):
                attacks |= 1 << tgt
    KNIGHT_ATTACKS[sq] = attacks


def knight_attacks(sq: int) -> int:
    """
    Return a bitboard of knight moves from the given square (0-63).
    """
    return KNIGHT_ATTACKS[sq]


def generate_knight_moves(
    knights_bb: int, my_occ: int, their_occ: int
) -> List[Move]:
    """
    Generate knight moves from square sq as a list of Move(src, dst).
    """

    moves: List[Move] = []
    tmp_knights = knights_bb
    while tmp_knights:
        src = pop_lsb(tmp_knights)
        attacks = KNIGHT_ATTACKS[src]
        legal = attacks & ~my_occ
        tmp = legal
        while tmp:
            dest = pop_lsb(tmp)
            is_capture = bool(their_occ & (1 << dest))
            moves.append(Move(src, dest, capture=is_capture))
            tmp &= tmp - 1
        tmp_knights &= tmp_knights - 1
    return moves
