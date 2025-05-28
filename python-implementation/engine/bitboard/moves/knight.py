from engine.bitboard.move import Move
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import FILE_A, FILE_H, KNIGHT_OFFSETS

# Precompute knight attack bitboards for all 64 squares
KNIGHT_ATTACKS = [0] * 64
for sq in range(64):
    attacks = 0
    src_mask = 1 << sq
    for offset in KNIGHT_OFFSETS:
        # wrap-around prevention for A-file
        if offset in (-17, -10, 6, 15) and (src_mask & FILE_A):
            continue
        # wrap-around prevention for H-file
        if offset in (-15, -6, 10, 17) and (src_mask & FILE_H):
            continue
        tgt = sq + offset
        if 0 <= tgt < 64:
            attacks |= 1 << tgt
    KNIGHT_ATTACKS[sq] = attacks


def knight_attacks(sq: int) -> int:
    """
    Return a bitboard of knight moves from the given square (0-63).
    """
    return KNIGHT_ATTACKS[sq]


def generate_knight_moves(sq: int) -> list[Move]:
    """
    Generate knight moves from square sq as a list of Move(src, dst).
    """
    moves: list[Move] = []
    bb = knight_attacks(sq)
    while bb:
        tgt = pop_lsb(bb)
        moves.append(Move(sq, tgt))
        bb &= bb - 1
    return moves
