from typing import List
from engine.bitboard.config import RawMove  # noqa: TC002
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import (
    MASK_64,
    RANK_2,
    RANK_4,
    RANK_5,
    RANK_7,
    FILE_A,
    FILE_H,
)


def pawn_single_push_targets(
    pawns_bb: int, all_occ: int, is_white: bool
) -> int:
    """
    Return a bitboard mask of all legal single-square pawn pushes
    for the given pawn bitboard and occupancy.
    """
    empty = (~all_occ) & MASK_64
    return (pawns_bb << 8) & empty if is_white else (pawns_bb >> 8) & empty


def pawn_double_push_targets(
    pawns_bb: int, all_occ: int, is_white: bool
) -> int:
    """
    Return a bitboard mask of all legal double-square pawn pushes
    for pawns on their starting rank.
    """
    empty = (~all_occ) & MASK_64
    if is_white:
        return ((pawns_bb & RANK_2) << 16) & empty & (empty << 8)
    else:
        return ((pawns_bb & RANK_7) >> 16) & empty & (empty >> 8)


def pawn_capture_targets(pawns_bb: int, enemy_bb: int, is_white: bool) -> int:
    """
    Return a bitboard mask of all legal pawn captures,
    given the pawn bitboard and the enemy-occupancy bitboard.
    """
    if is_white:
        left = (pawns_bb & ~FILE_A) << 7
        right = (pawns_bb & ~FILE_H) << 9
    else:
        left = (pawns_bb & ~FILE_A) >> 9
        right = (pawns_bb & ~FILE_H) >> 7
    return (left | right) & enemy_bb & MASK_64


def pawn_en_passant_targets(
    pawns_bb: int, ep_mask: int, is_white: bool
) -> int:
    """
    Return a bitboard mask of en-passant capture destinations,
    given the pawn bitboard, the ep_mask (1<<sq or 0), and the side to move.
    """
    if ep_mask == 0:
        return 0

    if is_white:
        # Only pawns on rank 5 can capture en passant
        # “downward” to an empty square on rank 6
        base = pawns_bb & RANK_5
        left = (base & ~FILE_A) << 7  # up-left
        right = (base & ~FILE_H) << 9  # up-right
    else:
        # Only pawns on rank 4 can capture en passant
        # “upward” to an empty square on rank 3
        base = pawns_bb & RANK_4
        left = (base & ~FILE_A) >> 9  # down-left
        right = (base & ~FILE_H) >> 7  # down-right

    return (left | right) & ep_mask & MASK_64


def generate_pawn_moves(
    pawns_bb: int,
    enemy_bb: int,
    all_occ: int,
    is_white: bool,
    ep_mask: int = 0,
) -> List[RawMove]:
    """
    Return all legal pawn moves: single/double pushes and diagonal captures.
    Every returned move is a RawMove tuple.
    """
    moves: List[RawMove] = []

    # --- Pushes (single and double) ---
    for step, helper in [
        (8, pawn_single_push_targets),
        (16, pawn_double_push_targets),
    ]:
        bb = helper(pawns_bb, all_occ, is_white)
        tmp = bb
        while tmp:
            dest = pop_lsb(tmp)
            src = dest - step if is_white else dest + step
            # Promotion check on single (8) pushes:
            if step == 8 and (
                (is_white and dest >= 56) or (not is_white and dest < 8)
            ):
                for promo in ("Q", "R", "B", "N"):
                    moves.append((src, dest, False, promo, False, False))
            else:
                moves.append((src, dest, False, None, False, False))
            tmp &= tmp - 1

    # --- Captures (fix: only if files are adjacent) ---
    cap_bb = pawn_capture_targets(pawns_bb, enemy_bb, is_white)
    tmp = cap_bb
    while tmp:
        dest = pop_lsb(tmp)
        df = dest % 8

        if is_white:
            # candidate src squares:
            src_left = dest - 7  # capture from file one to the right (df+1)
            src_right = dest - 9  # capture from file one to the left (df−1)

            # ONLY generate if files match up:
            #  - left capture is valid only if dest’s file < 7
            # (so src_left’s file = df+1 ≤7)
            if df < 7 and 0 <= src_left < 64 and ((pawns_bb >> src_left) & 1):
                if dest >= 56:  # promotion rank
                    for promo in ("Q", "R", "B", "N"):
                        moves.append(
                            (src_left, dest, True, promo, False, False)
                        )

                else:
                    moves.append((src_left, dest, True, None, False, False))

            #  - right capture is valid only if dest’s file > 0
            # (so src_right’s file = df−1 ≥0)
            if (
                df > 0
                and 0 <= src_right < 64
                and ((pawns_bb >> src_right) & 1)
            ):
                if dest >= 56:
                    for promo in ("Q", "R", "B", "N"):
                        moves.append(
                            (src_right, dest, True, promo, False, False)
                        )
                else:
                    moves.append((src_right, dest, True, None, False, False))

        else:
            # Black’s turn: downward captures
            src_left = dest + 9  # file one to the right (df+1)
            src_right = dest + 7  # file one to the left  (df−1)

            if df < 7 and 0 <= src_left < 64 and ((pawns_bb >> src_left) & 1):
                if dest < 8:  # promotion rank for Black
                    for promo in ("Q", "R", "B", "N"):
                        moves.append(
                            (src_left, dest, True, promo, False, False)
                        )

                else:
                    moves.append((src_left, dest, True, None, False, False))

            if (
                df > 0
                and 0 <= src_right < 64
                and ((pawns_bb >> src_right) & 1)
            ):
                if dest < 8:
                    for promo in ("Q", "R", "B", "N"):
                        moves.append(
                            (src_right, dest, True, promo, False, False)
                        )

                else:
                    moves.append((src_right, dest, True, None, False, False))

        tmp &= tmp - 1

    # --- En-passant captures (unchanged) ---
    ep_bb = pawn_en_passant_targets(pawns_bb, ep_mask, is_white)
    tmp = ep_bb
    while tmp:
        dest = pop_lsb(tmp)
        if is_white:
            src = dest - 7 if ((pawns_bb >> (dest - 7)) & 1) else dest - 9
        else:
            src = dest + 9 if ((pawns_bb >> (dest + 9)) & 1) else dest + 7

        moves.append((src, dest, True, None, True, False))

        tmp &= tmp - 1

    return moves
