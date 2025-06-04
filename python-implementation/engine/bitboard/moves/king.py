from typing import List
from engine.bitboard.move import Move  # noqa: TC002
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import KING_OFFSETS, FILE_A, FILE_H


def one_king_mask(sq):
    mask = 0
    for offset in KING_OFFSETS:
        dest = sq + offset
        if dest < 0 or dest > 63:
            continue
        origin_bb = 1 << sq
        # West-moving offsets that wrap from a-file
        if origin_bb & FILE_A and offset in (-1, 7, -9):
            continue

        # East-moving offsets that wrap from h-file
        if origin_bb & FILE_H and offset in (1, -7, 9):
            continue
        mask |= 1 << dest
    return mask


KING_ATTACKS = [0] * 64
for i in range(len(KING_ATTACKS)):
    KING_ATTACKS[i] = one_king_mask(i)


def generate_king_moves(
    king_bb: int, my_occ: int, their_occ: int
) -> List[Move]:
    """
    Appends all legal one-square king moves for the side to move.
    Castling will be added later.
    """
    moves: List[Move] = []

    if king_bb == 0:
        return moves

    src = pop_lsb(king_bb)
    targets = KING_ATTACKS[src] & ~my_occ

    while targets:
        dst = pop_lsb(targets)
        targets &= targets - 1
        is_capture = bool((1 << dst) & their_occ)
        moves.append(Move(src, dst, capture=is_capture))

    return moves
