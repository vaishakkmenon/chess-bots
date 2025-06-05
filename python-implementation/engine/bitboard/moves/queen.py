from typing import List, Union, Tuple
from engine.bitboard.config import USE_RAW_MOVES
from engine.bitboard.move import Move  # noqa: TC002
from engine.bitboard.utils import pop_lsb
from engine.bitboard.moves.rook import rook_attacks
from engine.bitboard.moves.bishop import bishop_attacks


def queen_attacks(sq: int, full_occ: int) -> int:
    """
    Combine my_occ and their_occ into a single occupancy bitboard,
    then return the union of rook_attacks and bishop_attacks on that occupancy.
    """
    return rook_attacks(sq, full_occ) | bishop_attacks(sq, full_occ)


def generate_queen_moves(
    queen_bb: int, my_occ: int, their_occ: int
) -> List[Union[Move, Tuple[int, int, bool, None, bool, bool]]]:
    """
    Given a bitboard of all queens for side-to-move, plus my_occ and their_occ,
    generate all legal queen moves.
    """
    moves: List[Union[Move, Tuple[int, int, bool, None, bool, bool]]] = []
    full_occ = my_occ | their_occ
    temp = queen_bb

    while temp:
        src = pop_lsb(temp)
        temp &= temp - 1

        attacks = queen_attacks(src, full_occ)
        legal = attacks & ~my_occ

        legal_temp = legal
        while legal_temp:
            dst = pop_lsb(legal_temp)
            legal_temp &= legal_temp - 1
            is_capture = bool(their_occ & (1 << dst))
            if USE_RAW_MOVES:
                moves.append((src, dst, is_capture, None, False, False))
            else:
                moves.append(Move(src, dst, capture=is_capture))
    return moves
