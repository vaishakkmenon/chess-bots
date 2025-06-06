import engine.bitboard.config as config
from typing import List, Union, Tuple, Optional
from engine.bitboard.move import Move  # noqa: TC002
from engine.bitboard.board import Board  # noqa: TC002
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
)

from engine.bitboard.moves.king import generate_king_moves
from engine.bitboard.moves.rook import generate_rook_moves
from engine.bitboard.moves.queen import generate_queen_moves
from engine.bitboard.moves.bishop import generate_bishop_moves
from engine.bitboard.moves.knight import (
    knight_attacks,
    generate_knight_moves,
)
from engine.bitboard.moves.pawn import (
    pawn_single_push_targets,
    pawn_double_push_targets,
    pawn_en_passant_targets,
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
    "pawn_en_passant_targets",
    "pawn_capture_targets",
    "generate_pawn_moves",
    # Bishop API
    "generate_bishop_moves",
    # Rook API
    "generate_rook_moves",
    # Queen API
    "generate_queen_moves",
    # King API
    "generate_king_moves",
]


def generate_moves(
    board: Board,
) -> List[Union[Move, Tuple[int, int, bool, Optional[str], bool, bool]]]:
    """
    Master move generator for the side to move.
    Calls each piece-type generator and collects all legal moves.
    """
    moves: List[
        Union[Move, Tuple[int, int, bool, Optional[str], bool, bool]]
    ] = []

    # Pawn moves (including en-passant)
    if board.side_to_move == WHITE:
        pawn_bb = board.bitboards[WHITE_PAWN]
        enemy_bb = board.black_occ
        is_white = True
    else:
        pawn_bb = board.bitboards[BLACK_PAWN]
        enemy_bb = board.white_occ
        is_white = False

    ep_mask = (1 << board.ep_square) if board.ep_square else 0

    moves += generate_pawn_moves(
        pawn_bb,
        enemy_bb,
        board.all_occ,
        is_white,
        ep_mask=ep_mask,
    )

    my_occ = board.white_occ if is_white else board.black_occ
    their_occ = board.black_occ if is_white else board.white_occ

    # Knight
    moves += generate_knight_moves(
        board.bitboards[WHITE_KNIGHT if is_white else BLACK_KNIGHT],
        my_occ,
        their_occ,
    )

    # Bishop
    moves += generate_bishop_moves(
        board.bitboards[WHITE_BISHOP if is_white else BLACK_BISHOP],
        my_occ,
        their_occ,
    )

    # Rook
    moves += generate_rook_moves(
        board.bitboards[WHITE_ROOK if is_white else BLACK_ROOK],
        my_occ,
        their_occ,
    )

    moves += generate_queen_moves(
        board.bitboards[WHITE_QUEEN if is_white else BLACK_QUEEN],
        my_occ,
        their_occ,
    )

    moves += generate_king_moves(
        board,
        board.bitboards[WHITE_KING if is_white else BLACK_KING],
        my_occ,
        their_occ,
    )
    return moves


def generate_legal_moves(
    board: Board,
) -> List[Union[Move, Tuple[int, int, bool, Optional[str], bool, bool]]]:
    """
    Wraps generate_moves(board) and returns only those moves
    that do not leave the side-to-move's king in check.
    """
    legal_moves: List[
        Union[Move, Tuple[int, int, bool, Optional[str], bool, bool]]
    ] = []
    side = board.side_to_move

    pseudo_moves = generate_moves(board)
    for move in pseudo_moves:
        if config.USE_RAW_MOVES:
            board.make_move_raw(move)
        else:
            board.make_move(move)

        if not board.in_check(side):
            legal_moves.append(move)

        if config.USE_RAW_MOVES:
            board.undo_move_raw()
        else:
            board.undo_move()

    return legal_moves
