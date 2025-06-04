from __future__ import annotations

from typing import TYPE_CHECKING

from engine.bitboard.moves.knight import KNIGHT_ATTACKS
from engine.bitboard.moves.bishop import bishop_attacks
from engine.bitboard.moves.rook import rook_attacks
from engine.bitboard.constants import (
    WHITE_PAWN,
    BLACK_PAWN,
    WHITE_KNIGHT,
    BLACK_KNIGHT,
    WHITE_BISHOP,
    BLACK_BISHOP,
    WHITE_ROOK,
    BLACK_ROOK,
    WHITE_QUEEN,
    BLACK_QUEEN,
    WHITE_KING,
    BLACK_KING,
    WHITE,
    BLACK,
)

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .board import Board


def is_square_attacked(board: "Board", square: int, attacker_side: int) -> bool:
    """Return True if ``square`` is attacked by ``attacker_side``."""
    all_occ = board.white_occ | board.black_occ

    # 1. Pawn attacks
    if attacker_side == WHITE:
        pawn_bb = board.bitboards[WHITE_PAWN]
        mask = 0
        if square >= 9 and (square % 8) != 7:
            mask |= 1 << (square - 9)
        if square >= 7 and (square % 8) != 0:
            mask |= 1 << (square - 7)
        if pawn_bb & mask:
            return True
    else:
        pawn_bb = board.bitboards[BLACK_PAWN]
        mask = 0
        if square <= 56 and (square % 8) != 7:
            mask |= 1 << (square + 7)
        if square <= 55 and (square % 8) != 0:
            mask |= 1 << (square + 9)
        if pawn_bb & mask:
            return True

    # 2. Knight attacks
    knight_bb = (
        board.bitboards[WHITE_KNIGHT]
        if attacker_side == WHITE
        else board.bitboards[BLACK_KNIGHT]
    )
    if KNIGHT_ATTACKS[square] & knight_bb:
        return True

    # 3. Bishop/Queen diagonal attacks
    diagonal_attackers = (
        board.bitboards[WHITE_BISHOP] | board.bitboards[WHITE_QUEEN]
        if attacker_side == WHITE
        else board.bitboards[BLACK_BISHOP] | board.bitboards[BLACK_QUEEN]
    )
    if bishop_attacks(square, all_occ) & diagonal_attackers:
        return True

    # 4. Rook/Queen orthogonal attacks
    orthogonal_attackers = (
        board.bitboards[WHITE_ROOK] | board.bitboards[WHITE_QUEEN]
        if attacker_side == WHITE
        else board.bitboards[BLACK_ROOK] | board.bitboards[BLACK_QUEEN]
    )
    if rook_attacks(square, all_occ) & orthogonal_attackers:
        return True

    # 5. King attacks (adjacent)
    from engine.bitboard.moves.king import KING_ATTACKS

    king_bb = (
        board.bitboards[WHITE_KING]
        if attacker_side == WHITE
        else board.bitboards[BLACK_KING]
    )
    if KING_ATTACKS[square] & king_bb:
        return True

    return False
