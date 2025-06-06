# engine/bitboard/moves/king.py

from typing import List, TYPE_CHECKING
from engine.bitboard.config import RawMove  # noqa: TC002
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


def one_king_mask(sq: int) -> int:
    """
    Return a bitboard mask of all adjacent squares to `sq` (0..63),
    ignoring occupancy but avoiding wraparound off the board.
    """
    mask = 0
    for offset in KING_OFFSETS:
        dest = sq + offset
        if dest < 0 or dest > 63:
            continue
        origin_bb = 1 << sq

        # Prevent wrap from A-file to H-file
        if origin_bb & FILE_A and offset in (-1, 7, -9):
            continue

        # Prevent wrap from H-file to A-file
        if origin_bb & FILE_H and offset in (1, -7, 9):
            continue

        mask |= 1 << dest

    return mask


# Precompute king‐attack masks for every square
KING_ATTACKS: List[int] = [0] * 64
for i in range(64):
    KING_ATTACKS[i] = one_king_mask(i)


def generate_king_moves(
    board: "Board",
    king_bb: int,
    my_occ: int,
    their_occ: int,
) -> List[RawMove]:
    """
    Generate all *legal* king moves
    (one-square steps and castling) for the side to move.
    One-square steps that land on an attacked square are filtered out here.
    Castling moves are also fully validated
        (empty squares + no attacked squares).
    """
    moves: List[RawMove] = []

    # No king bit found → no moves
    if king_bb == 0:
        return moves

    # There should be exactly one king bit
    src = pop_lsb(king_bb)

    # Phase 1: Generate one‐square steps,
    # filtering out any destination attacked by opponent
    potential = KING_ATTACKS[src] & ~my_occ
    opponent = BLACK if board.side_to_move == WHITE else WHITE

    while potential:
        dst = pop_lsb(potential)
        potential &= potential - 1

        # If destination is not attacked, it is legal
        if not board.is_square_attacked(dst, opponent):
            is_capture = bool((1 << dst) & their_occ)
            moves.append((src, dst, is_capture, None, False, False))

    # Phase 2: Castling (fully validated as before)
    rights = board.castling_rights

    if board.side_to_move == WHITE:
        # King must be on e1 (4) to castle
        if src == 4:
            # White kingside (bit 0)
            if rights & 0b0001:
                # f1 (5) and g1 (6) must be empty
                if not (board.all_occ & ((1 << 5) | (1 << 6))):
                    # Rook on h1 (7) must be present
                    if board.bitboards[WHITE_ROOK] & (1 << 7):
                        # e1, f1, g1 must not be attacked
                        if (
                            not is_square_attacked(board, 4, BLACK)
                            and not is_square_attacked(board, 5, BLACK)
                            and not is_square_attacked(board, 6, BLACK)
                        ):

                            moves.append((src, 6, False, None, False, True))

            # White queenside (bit 1)
            if rights & 0b0010:
                # b1 (1), c1 (2), d1 (3) must be empty
                if not (board.all_occ & ((1 << 1) | (1 << 2) | (1 << 3))):
                    # Rook on a1 (0) must be present
                    if board.bitboards[WHITE_ROOK] & (1 << 0):
                        # e1, d1, c1 must not be attacked
                        if (
                            not is_square_attacked(board, 4, BLACK)
                            and not is_square_attacked(board, 3, BLACK)
                            and not is_square_attacked(board, 2, BLACK)
                        ):

                            moves.append((src, 2, False, None, False, True))

    else:
        # Black to move; king must be on e8 (60)
        if src == 60:
            # Black kingside (bit 2)
            if rights & 0b0100:
                if not (board.all_occ & ((1 << 61) | (1 << 62))):
                    if board.bitboards[BLACK_ROOK] & (1 << 63):
                        if (
                            not is_square_attacked(board, 60, WHITE)
                            and not is_square_attacked(board, 61, WHITE)
                            and not is_square_attacked(board, 62, WHITE)
                        ):

                            moves.append((src, 62, False, None, False, True))

            # Black queenside (bit 3)
            if rights & 0b1000:
                if not (board.all_occ & ((1 << 57) | (1 << 58) | (1 << 59))):
                    if board.bitboards[BLACK_ROOK] & (1 << 56):
                        if (
                            not is_square_attacked(board, 60, WHITE)
                            and not is_square_attacked(board, 59, WHITE)
                            and not is_square_attacked(board, 58, WHITE)
                        ):

                            moves.append((src, 58, False, None, False, True))

    return moves
