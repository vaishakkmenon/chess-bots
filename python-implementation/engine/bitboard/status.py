# engine/bitboard/status.py

from engine.bitboard.board import Board  # noqa: TC002
from engine.bitboard.generator import generate_legal_moves
from engine.bitboard.constants import (
    WHITE_KNIGHT,
    WHITE_BISHOP,
    WHITE_ROOK,
    WHITE_QUEEN,
    WHITE_PAWN,
    BLACK_KNIGHT,
    BLACK_BISHOP,
    BLACK_ROOK,
    BLACK_QUEEN,
    BLACK_PAWN,
)


def is_stalemate(board: Board) -> bool:
    """
    Stalemate: side to move is NOT in check, but has no legal moves.
    """
    side = board.side_to_move
    return not board.in_check(side) and len(generate_legal_moves(board)) == 0


def is_checkmate(board: Board) -> bool:
    """
    Checkmate: side to move IS in check, and has no legal moves.
    """
    side = board.side_to_move
    return board.in_check(side) and len(generate_legal_moves(board)) == 0


def is_insufficient_material(board: Board) -> bool:
    """
    True if neither side has sufficient material to force mate.
    Covers:
      - King vs King
      - King + single minor (bishop or knight) vs King
      - King + Bishop(s) vs King + Bishop(s) when all bishops are on same color
    """
    # pull out piece bitboards
    wb = board.bitboards

    # helper to count bits
    def cnt(bb: int) -> int:
        return bb.bit_count()

    # count non-king pieces for each side
    white_minors = cnt(wb[WHITE_KNIGHT]) + cnt(wb[WHITE_BISHOP])
    white_majors = (
        cnt(wb[WHITE_ROOK]) + cnt(wb[WHITE_QUEEN]) + cnt(wb[WHITE_PAWN])
    )
    black_minors = cnt(wb[BLACK_KNIGHT]) + cnt(wb[BLACK_BISHOP])
    black_majors = (
        cnt(wb[BLACK_ROOK]) + cnt(wb[BLACK_QUEEN]) + cnt(wb[BLACK_PAWN])
    )

    # 1) King vs King
    if white_minors == black_minors == 0 and white_majors == black_majors == 0:
        return True

    # 2) King + single minor vs King
    if white_majors == 0 and black_majors == 0:
        if (white_minors == 1 and black_minors == 0) or (
            black_minors == 1 and white_minors == 0
        ):
            return True

    # 3) King + bishops only, and all bishops on same color
    bishops_bb = wb[WHITE_BISHOP] | wb[BLACK_BISHOP]
    if (
        white_majors == black_majors == 0
        and (white_minors + black_minors) >= 2
    ):
        light_mask = 0x55AA55AA55AA55AA  # precomputed light-square mask
        dark_mask = ~light_mask & ((1 << 64) - 1)
        if (bishops_bb & light_mask == 0) or (bishops_bb & dark_mask == 0):
            return True

    return False
