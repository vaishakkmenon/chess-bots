from engine.bitboard.board import Board  # noqa: TC002
from engine.bitboard.move import Move  # noqa: TC002
from engine.bitboard.constants import (
    WHITE_PAWN,
    BLACK_PAWN,
    WHITE_KNIGHT,
    BLACK_KNIGHT,
    WHITE,
)

from engine.bitboard.moves.knight import (
    knight_attacks,
    generate_knight_moves,
)
from engine.bitboard.moves.pawn import (
    pawn_single_push_targets,
    pawn_double_push_targets,
    pawn_push_targets,
    pawn_capture_targets,
    generate_pawn_moves,
)

__all__ = [
    # Knight API
    "knight_attacks",
    "generate_knight_moves",
    # Pawn API
    "pawn_single_push_targets",
    "pawn_double_push_targets",
    "pawn_push_targets",
    "pawn_capture_targets",
    "generate_pawn_moves",
]


def generate_moves(board: Board) -> list[Move]:
    """
    Master move generator for the side to move.
    Calls each piece-type generator and collects all legal moves.
    """
    moves: list[Move] = []

    # 1) Pawn moves (including en-passant)
    if board.side_to_move == WHITE:
        pawn_bb = board.bitboards[WHITE_PAWN]
        enemy_bb = board.black_occ
        is_white = True
    else:
        pawn_bb = board.bitboards[BLACK_PAWN]
        enemy_bb = board.white_occ
        is_white = False

    moves += generate_pawn_moves(
        pawn_bb, enemy_bb, board.all_occ, is_white, ep_mask=board.ep_square
    )

    # 2) Knight moves (example)
    moves += generate_knight_moves(
        board.bitboards[WHITE_KNIGHT if is_white else BLACK_KNIGHT],
        board.white_occ if is_white else board.black_occ,
        board.black_occ if is_white else board.white_occ,
    )

    return moves
