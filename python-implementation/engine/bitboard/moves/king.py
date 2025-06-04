from __future__ import annotations

from typing import List, TYPE_CHECKING

from engine.bitboard.move import Move  # noqa: TC002
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import (
    KING_OFFSETS,
    FILE_A,
    FILE_H,
    WHITE,
    BLACK,
    WHITE_ROOK,
    BLACK_ROOK,
)
from engine.bitboard.attack_utils import is_square_attacked

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from engine.bitboard.board import Board


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
    board: "Board",
    king_bb: int,
    my_occ: int,
    their_occ: int,
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

    # Castling moves
    side = WHITE if board.side_to_move == WHITE else BLACK
    if side == WHITE:
        rights = board.castling_rights
        # White kingside
        if rights & 0b0001 and src == 4:
            empty = not (board.all_occ & ((1 << 5) | (1 << 6)))
            rook_ready = board.bitboards[WHITE_ROOK] & (1 << 7)
            if (
                empty
                and rook_ready
                and not is_square_attacked(board, 4, BLACK)
                and not is_square_attacked(board, 5, BLACK)
                and not is_square_attacked(board, 6, BLACK)
            ):
                moves.append(Move(src, 6))

        # White queenside
        if rights & 0b0010 and src == 4:
            empty = not (board.all_occ & ((1 << 1) | (1 << 2) | (1 << 3)))
            rook_ready = board.bitboards[WHITE_ROOK] & (1 << 0)
            if (
                empty
                and rook_ready
                and not is_square_attacked(board, 4, BLACK)
                and not is_square_attacked(board, 3, BLACK)
                and not is_square_attacked(board, 2, BLACK)
            ):
                moves.append(Move(src, 2))
    else:
        rights = board.castling_rights
        if rights & 0b0100 and src == 60:
            empty = not (board.all_occ & ((1 << 61) | (1 << 62)))
            rook_ready = board.bitboards[BLACK_ROOK] & (1 << 63)
            if (
                empty
                and rook_ready
                and not is_square_attacked(board, 60, WHITE)
                and not is_square_attacked(board, 61, WHITE)
                and not is_square_attacked(board, 62, WHITE)
            ):
                moves.append(Move(src, 62))

        if rights & 0b1000 and src == 60:
            empty = not (board.all_occ & ((1 << 57) | (1 << 58) | (1 << 59)))
            rook_ready = board.bitboards[BLACK_ROOK] & (1 << 56)
            if (
                empty
                and rook_ready
                and not is_square_attacked(board, 60, WHITE)
                and not is_square_attacked(board, 59, WHITE)
                and not is_square_attacked(board, 58, WHITE)
            ):
                moves.append(Move(src, 58))

    return moves
