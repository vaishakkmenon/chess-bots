# tests/test_move_counters_raw_comprehensive.py

from engine.bitboard.move import Move
from engine.bitboard.board import Board
from engine.bitboard.utils import move_to_tuple
from engine.bitboard.constants import (
    WHITE,
    BLACK,
    WHITE_KNIGHT,
    BLACK_PAWN,
    WHITE_KING,
    BLACK_KING,
    WHITE_ROOK,
)


def make_empty_board() -> Board:
    b = Board()
    # clear to absolute empty
    b.bitboards = [0] * 12
    b.white_occ = b.black_occ = b.all_occ = 0
    b.castling_rights = 0
    b.ep_square = None
    b.side_to_move = WHITE
    b.halfmove_clock = 0
    b.fullmove_number = 1
    b.raw_history.clear()
    # rebuild square_to_piece
    b.square_to_piece = [None] * 64
    return b


def place_piece(b: Board, piece_idx: int, sq: int):
    b.bitboards[piece_idx] |= 1 << sq
    b.update_occupancies()
    # rebuild square_to_piece
    b.square_to_piece = [None] * 64
    for idx, bb in enumerate(b.bitboards):
        while bb:
            lsb = bb & -bb
            s = lsb.bit_length() - 1
            b.square_to_piece[s] = idx
            bb ^= lsb


def apply_raw(b: Board, move: Move):
    """Convert Move→RawMove tuple and apply via make_move_raw."""
    raw = move_to_tuple(move)
    b.make_move_raw(raw)


def test_initial_counters():
    b = Board()
    assert (b.fullmove_number, b.halfmove_clock, b.side_to_move) == (
        1,
        0,
        WHITE,
    )


def test_single_pawn_move_resets():
    b = Board()
    # 1. e4
    apply_raw(b, Move(src=12, dst=28, capture=False))
    assert (b.halfmove_clock, b.fullmove_number, b.side_to_move) == (
        0,
        1,
        BLACK,
    )


def test_double_pawn_push_resets_and_fullmove():
    b = Board()
    apply_raw(b, Move(12, 28))  # 1. e4
    apply_raw(b, Move(51, 35))  # 1... d5
    assert (b.halfmove_clock, b.fullmove_number, b.side_to_move) == (
        0,
        2,
        WHITE,
    )


def test_knight_move_increments():
    b = Board()
    apply_raw(b, Move(src=6, dst=21, capture=False))
    assert (b.halfmove_clock, b.fullmove_number, b.side_to_move) == (
        1,
        1,
        BLACK,
    )


def test_capture_resets():
    b = make_empty_board()
    # setup b1 Knight vs c3 pawn
    place_piece(b, WHITE_KNIGHT, 1)
    place_piece(b, BLACK_PAWN, 18)
    apply_raw(b, Move(src=1, dst=18, capture=True))
    assert (b.halfmove_clock, b.fullmove_number, b.side_to_move) == (
        0,
        1,
        BLACK,
    )


def test_en_passant_resets_and_fullmove():
    b = make_empty_board()
    # Setup kings and pawns for en-passant
    place_piece(b, WHITE_KING, 4)
    place_piece(b, BLACK_KING, 60)
    place_piece(b, 0, 28)  # WHITE_PAWN on e5
    place_piece(b, 6, 51)  # BLACK_PAWN on d7

    # 1... d7→d5 (Black to move)
    b.side_to_move = BLACK
    apply_raw(b, Move(src=51, dst=35, capture=False, en_passant=True))
    # After Black’s move: halfmove reset, fullmove→2, White to move
    assert (b.halfmove_clock, b.fullmove_number, b.side_to_move) == (
        0,
        2,
        WHITE,
    )

    # 2. exd6 e.p. (White to move)
    b.side_to_move = WHITE
    apply_raw(b, Move(src=28, dst=43, capture=True, en_passant=True))
    # After White’s capture: halfmove reset, fullmove stays 2, Black to move
    assert (b.halfmove_clock, b.fullmove_number, b.side_to_move) == (
        0,
        2,
        BLACK,
    )


def test_castling_increments():
    b = make_empty_board()
    # setup white king and rook for castling
    place_piece(b, WHITE_KING, 4)  # e1
    place_piece(b, WHITE_ROOK, 7)  # h1
    b.castling_rights = 0b0011  # allow both
    apply_raw(b, Move(src=4, dst=6, castling=True))
    assert (b.halfmove_clock, b.fullmove_number, b.side_to_move) == (
        1,
        1,
        BLACK,
    )


def test_fullmove_increments_only_after_black():
    b = Board()
    apply_raw(b, Move(12, 28))  # 1. e4
    apply_raw(b, Move(51, 35))  # 1...d5
    assert b.fullmove_number == 2 and b.side_to_move == WHITE
    apply_raw(b, Move(6, 21))  # 2. Nf3
    assert b.fullmove_number == 2 and b.side_to_move == BLACK
