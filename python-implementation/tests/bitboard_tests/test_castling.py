import pytest

from engine.bitboard.board import Board
from engine.bitboard.move import Move
from engine.bitboard.constants import (
    WHITE,
    WHITE_KING,
    WHITE_ROOK,
    WHITE_PAWN,
    BLACK_QUEEN,
    BLACK_ROOK,
)
from engine.bitboard.moves.king import generate_king_moves

PIECE_INDEX = {
    "K": WHITE_KING,
    "R": WHITE_ROOK,
    "P": WHITE_PAWN,
    "q": BLACK_QUEEN,
    "r": BLACK_ROOK,
}


def sq(file: int, rank: int) -> int:
    return (rank - 1) * 8 + (file - 1)


def make_board(pieces: dict[int, str]) -> Board:
    board = Board()
    board.bitboards = [0] * 12
    for square, char in pieces.items():
        board.bitboards[PIECE_INDEX[char]] |= 1 << square
    board.update_occupancies()
    board.side_to_move = WHITE
    return board


@pytest.mark.parametrize(
    "rook_sq,to_sq,rights",
    [
        (sq(8, 1), sq(7, 1), 0b0001),
        (sq(1, 1), sq(3, 1), 0b0010),
    ],
)
def test_castling_allowed(rook_sq: int, to_sq: int, rights: int) -> None:
    board = make_board({sq(5, 1): "K", rook_sq: "R"})
    board.castling_rights = rights
    moves = generate_king_moves(
        board,
        board.bitboards[WHITE_KING],
        board.white_occ,
        board.black_occ,
    )
    assert any(m.src == sq(5, 1) and m.dst == to_sq for m in moves)


def test_castling_blocked_path() -> None:
    board = make_board({sq(5, 1): "K", sq(8, 1): "R", sq(6, 1): "P"})
    board.castling_rights = 0b0001
    moves = generate_king_moves(
        board,
        board.bitboards[WHITE_KING],
        board.white_occ,
        board.black_occ,
    )
    assert not any(m.src == sq(5, 1) and m.dst == sq(7, 1) for m in moves)


def test_castling_king_in_check() -> None:
    board = make_board({sq(5, 1): "K", sq(8, 1): "R", sq(5, 8): "q"})
    board.castling_rights = 0b0001
    moves = generate_king_moves(
        board,
        board.bitboards[WHITE_KING],
        board.white_occ,
        board.black_occ,
    )
    assert not any(m.src == sq(5, 1) and m.dst == sq(7, 1) for m in moves)


def test_castling_crossed_square_attacked() -> None:
    board = make_board({sq(5, 1): "K", sq(8, 1): "R", sq(6, 8): "q"})
    board.castling_rights = 0b0001
    moves = generate_king_moves(
        board,
        board.bitboards[WHITE_KING],
        board.white_occ,
        board.black_occ,
    )
    assert not any(m.src == sq(5, 1) and m.dst == sq(7, 1) for m in moves)


def test_castling_king_not_home() -> None:
    board = make_board({sq(4, 1): "K", sq(8, 1): "R"})
    board.castling_rights = 0b0001
    moves = generate_king_moves(
        board,
        board.bitboards[WHITE_KING],
        board.white_occ,
        board.black_occ,
    )
    assert not any(m.src == sq(4, 1) and m.dst == sq(6, 1) for m in moves)


@pytest.mark.parametrize(
    "start,end,mask",
    [
        (sq(5, 1), sq(5, 2), 0b0011),
        (sq(1, 1), sq(1, 2), 0b0010),
        (sq(8, 1), sq(8, 2), 0b0001),
        (sq(2, 1), sq(1, 1), 0b0010),
        (sq(7, 1), sq(8, 1), 0b0001),
    ],
)
def test_castling_rights_cleared_and_restored(start: int, end: int, mask: int) -> None:
    piece = "K" if start == sq(5, 1) else "R"
    board = make_board({start: piece})
    board.castling_rights = mask
    before = board.castling_rights
    board.make_move(Move(src=start, dst=end))
    assert board.castling_rights == 0
    board.undo_move()
    assert board.castling_rights == before


def test_castling_destination_attacked() -> None:
    board = make_board({sq(5, 1): "K", sq(8, 1): "R", sq(7, 8): "q"})
    board.castling_rights = 0b0001
    moves = generate_king_moves(
        board,
        board.bitboards[WHITE_KING],
        board.white_occ,
        board.black_occ,
    )
    assert not any(m.src == sq(5, 1) and m.dst == sq(7, 1) for m in moves)


def test_castling_crossed_square_attacked_queenside() -> None:
    board = make_board({sq(5, 1): "K", sq(1, 1): "R", sq(4, 8): "q"})
    board.castling_rights = 0b0010
    moves = generate_king_moves(
        board,
        board.bitboards[WHITE_KING],
        board.white_occ,
        board.black_occ,
    )
    assert not any(m.src == sq(5, 1) and m.dst == sq(3, 1) for m in moves)


def test_castling_no_rook_piece() -> None:
    board = make_board({sq(5, 1): "K"})
    board.castling_rights = 0b0001
    moves = generate_king_moves(
        board,
        board.bitboards[WHITE_KING],
        board.white_occ,
        board.black_occ,
    )
    assert not any(m.src == sq(5, 1) and m.dst == sq(7, 1) for m in moves)


def test_castling_with_enemy_rook_illegal() -> None:
    board = make_board({sq(5, 1): "K", sq(8, 1): "r"})
    board.castling_rights = 0b0001
    moves = generate_king_moves(
        board,
        board.bitboards[WHITE_KING],
        board.white_occ,
        board.black_occ,
    )
    assert not any(m.src == sq(5, 1) and m.dst == sq(7, 1) for m in moves)


def test_castling_move_execution_and_undo() -> None:
    board = make_board({sq(5, 1): "K", sq(8, 1): "R"})
    board.castling_rights = 0b0001
    move = Move(src=sq(5, 1), dst=sq(7, 1), castling=True)
    board.make_move(move)
    assert (board.bitboards[WHITE_KING] & (1 << sq(7, 1))) != 0
    assert (board.bitboards[WHITE_ROOK] & (1 << sq(6, 1))) != 0
    assert board.castling_rights == 0
    board.undo_move()
    assert (board.bitboards[WHITE_KING] & (1 << sq(5, 1))) != 0
    assert (board.bitboards[WHITE_ROOK] & (1 << sq(8, 1))) != 0
    assert board.castling_rights == 0b0001
