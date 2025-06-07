# tests/test_status_via_board.py

from engine.bitboard.board import Board  # noqa:TC001
from engine.bitboard.status import (
    is_stalemate,
    is_checkmate,
    is_insufficient_material,
    is_fifty_move_draw,
    is_threefold_repetition,
)
from engine.bitboard.constants import (
    WHITE_KING,
    BLACK_KING,
    WHITE_QUEEN,
    WHITE_ROOK,
    WHITE_BISHOP,
    WHITE_KNIGHT,
)


def rebuild_square_to_piece(board: Board) -> None:
    """
    Recompute board.square_to_piece from board.bitboards,
    exactly as Board.__init__ does.
    """
    board.square_to_piece = [None] * 64
    for idx, bb in enumerate(board.bitboards):
        b = bb
        while b:
            lsb = b & -b
            sq = lsb.bit_length() - 1
            board.square_to_piece[sq] = idx
            b ^= lsb


def make_empty_board() -> Board:
    b = Board()
    # clear out initial position
    b.bitboards = [0] * 12
    b.white_occ = b.black_occ = b.all_occ = 0
    b.ep_square = None
    b.castling_rights = 0
    b.side_to_move = 0  # White to move by default
    # history doesn’t matter here
    return b


def place_piece(board: Board, piece_idx: int, sq: int):
    """Place a single piece and recompute occupancies/mappings."""
    board.bitboards[piece_idx] |= 1 << sq
    board.update_occupancies()  # rebuild white_occ, black_occ, all_occ
    rebuild_square_to_piece(board)


def test_insufficient_material_kings_only():
    b = make_empty_board()
    place_piece(b, WHITE_KING, 4)  # e1
    place_piece(b, BLACK_KING, 60)  # e8
    assert is_insufficient_material(b)


def test_insufficient_material_knight_vs_king():
    b = make_empty_board()
    place_piece(b, WHITE_KING, 4)
    place_piece(b, BLACK_KING, 60)
    place_piece(b, WHITE_KNIGHT, 1)  # b1
    assert is_insufficient_material(b)


def test_insufficient_material_two_bishops_same_color():
    b = make_empty_board()
    place_piece(b, WHITE_KING, 4)
    place_piece(b, BLACK_KING, 60)
    # both bishops on light squares: c1 (2) and f4 (29)
    place_piece(b, WHITE_BISHOP, 2)
    place_piece(b, WHITE_BISHOP, 29)
    assert is_insufficient_material(b)


def test_not_insufficient_if_rook_present():
    b = make_empty_board()
    place_piece(b, WHITE_KING, 4)  # e1
    place_piece(b, BLACK_KING, 60)  # 38
    place_piece(b, WHITE_ROOK, 0)  # a1
    assert not is_insufficient_material(b)


def test_simple_stalemate():
    b = make_empty_board()
    # Black to move, classic corner stalemate:
    place_piece(b, BLACK_KING, 63)  # h8
    place_piece(b, WHITE_KING, 13)  # f2
    place_piece(b, WHITE_QUEEN, 46)  # g6
    b.side_to_move = 1  # BLACK
    assert is_stalemate(b)
    assert not is_checkmate(b)


def test_simple_checkmate():
    b = make_empty_board()
    place_piece(b, WHITE_KING, 17)  # b3
    place_piece(b, WHITE_ROOK, 7)  # h1
    place_piece(b, BLACK_KING, 1)  # b1
    b.side_to_move = 1  # Black to move
    assert is_checkmate(b)


def test_fifty_move_draw():
    b = Board()
    b.halfmove_clock = 99
    assert not is_fifty_move_draw(b)
    b.halfmove_clock = 100
    assert is_fifty_move_draw(b)


def test_threefold_repetition_via_hash_history():
    b = Board()
    # Starting position is in history once
    # Append two more identical entries
    b.zobrist_history.append(b.zobrist_key)
    b.zobrist_history.append(b.zobrist_key)
    assert is_threefold_repetition(b)

    # Only two copies = not yet repetition
    b2 = Board()
    b2.zobrist_history.append(b2.zobrist_key)
    assert not is_threefold_repetition(b2)
