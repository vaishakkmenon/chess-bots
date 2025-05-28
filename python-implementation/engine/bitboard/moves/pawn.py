from typing import List

from engine.bitboard.move import Move  # noqa: TC002
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import MASK_64, RANK_2, RANK_7, FILE_A, FILE_H


def pawn_single_push_targets(
    pawns_bb: int, all_occ: int, is_white: bool
) -> int:
    """
    Return a bitboard mask of all legal single-square pawn pushes
    for the given pawn bitboard and occupancy.
    """
    empty = (~all_occ) & MASK_64
    if is_white:
        return (pawns_bb << 8) & empty
    else:
        return (pawns_bb >> 8) & empty


def pawn_double_push_targets(
    pawns_bb: int, all_occ: int, is_white: bool
) -> int:
    """
    Return a bitboard mask of all legal double-square pawn pushes
    for pawns on their starting rank.
    """
    empty = (~all_occ) & MASK_64
    if is_white:
        start_pawns = pawns_bb & RANK_2
        one_move = start_pawns << 8 & empty
        two_move = (one_move << 8) & empty
        return two_move
    else:
        start_pawns = pawns_bb & RANK_7
        one_move = start_pawns >> 8 & empty
        two_move = (one_move >> 8) & empty
        return two_move


def pawn_push_targets(pawns_bb: int, all_occ: int, is_white: bool) -> int:
    """
    Return a bitboard mask combining single- and double-push targets.
    """
    return pawn_single_push_targets(
        pawns_bb, all_occ, is_white
    ) | pawn_double_push_targets(pawns_bb, all_occ, is_white)


def pawn_capture_targets(pawns_bb: int, enemy_bb: int, is_white: bool) -> int:
    """
    Return a bitboard mask of all legal pawn captures,
    given the pawn bitboard and the enemy-occupancy bitboard.
    """
    if is_white:
        left = (pawns_bb & ~FILE_A) << 7
        right = (pawns_bb & ~FILE_H) << 9
    else:
        left = (pawns_bb & ~FILE_H) >> 9
        right = (pawns_bb & ~FILE_A) >> 7

    return (left | right) & enemy_bb & MASK_64


def generate_pawn_moves(
    pawns_bb: int, enemy_bb: int, all_occ: int, is_white: bool
) -> list[Move]:
    """
    Return all legal pawn moves: single/double pushes and diagonal captures.
    """
    moves: List[Move] = []

    # --- Pushes (single and double) ---
    tests = [(8, pawn_single_push_targets), (16, pawn_double_push_targets)]
    for step, helper in tests:
        bb = helper(pawns_bb, all_occ, is_white)
        tmp = bb
        while tmp:
            dst = pop_lsb(tmp)
            src = dst - step if is_white else dst + step
            moves.append(Move(src, dst))
            tmp &= tmp - 1

    # --- Captures ---
    if is_white:
        left = (pawns_bb & ~FILE_A) << 7
    else:
        left = (pawns_bb & ~FILE_H) >> 9

    cap_bb = pawn_capture_targets(pawns_bb, enemy_bb, is_white)
    tmp = cap_bb
    while tmp:
        dst = pop_lsb(tmp)
        if (1 << dst) & left:
            src = dst - 7 if is_white else dst + 9
        else:
            src = dst - 9 if is_white else dst + 7

        moves.append(Move(src, dst, capture=True))
        tmp &= tmp - 1

    return moves
