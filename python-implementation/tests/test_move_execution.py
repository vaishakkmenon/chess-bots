import pytest
from engine.board import Board
from engine.moves.move import Move
from tests.utils import (
    make_board,
    print_section,
)


def test_make_and_undo():
    print_section("Move Execution and Undo")
    b = make_board({(5, 2): "P", (5, 7): "p"})
    move = Move((5, 2), (5, 4))
    ep_before = b.en_passant_target
    rights_before = b.make_move(move)
    b.undo_move(move, rights_before)
    assert b[(5, 2)] == "P"
    assert b[(5, 4)] == b.EMPTY
    assert b.en_passant_target == ep_before
    print("✔️ make_move and undo_move are consistent")


def test_undo_promotion():
    print_section("Undo Promotion Test")

    b = make_board({(7, 7): "P"})
    move = Move((7, 7), (7, 8), promo="Q")
    rights = b.make_move(move)
    assert b[(7, 8)] == "Q", "Piece must promote to Queen"
    b.undo_move(move, rights)
    assert b[(7, 7)] == "P", "Undo must restore pawn"
    assert b[(7, 8)] == Board.EMPTY, "Promotion square must be cleared"
    print("✔️ Undo promotion restores pawn correctly.")


# ─── Helpers ──────────────────────────────────────────────────────────────
def _round_trip(board, move):
    rights = board.make_move(move)
    board.undo_move(move, rights)


# ─── Capture round‑trip ───────────────────────────────────────────────────
def test_undo_capture_restores_position():
    b = make_board({(5, 5): "P", (5, 6): "p", (5, 1): "K", (5, 8): "k"})
    move = Move((5, 5), (5, 6))
    _round_trip(b, move)
    assert b[(5, 5)] == "P" and b[(5, 6)] == "p"


# ─── En‑passant make / undo ───────────────────────────────────────────────
def test_undo_en_passant_round_trip():
    # set up: white pawn e2, black pawn d4 after e2‑e4
    b = make_board({(5, 2): "P", (4, 4): "p", (5, 1): "K", (5, 8): "k"})
    # white double push
    dbl = Move((5, 2), (5, 4))
    b.make_move(dbl)
    b.en_passant = (5, 3)
    # black EP capture d4×e3
    ep = Move((4, 4), (5, 3), is_en_passant=True)
    _round_trip(b, ep)
    assert b[(4, 4)] == "p" and b[(5, 3)] == b.EMPTY and b[(5, 4)] == "P"


# ─── Castling make / undo ─────────────────────────────────────────────────
@pytest.mark.parametrize("rook_sq,to_sq", [((8, 1), (7, 1)), ((1, 1), (3, 1))])
def test_undo_castling_round_trip(rook_sq, to_sq):
    b = make_board({(5, 1): "K", rook_sq: "R", (5, 8): "k"})
    if rook_sq[0] == 8:
        b.white_can_castle_kingside = True
    else:
        b.white_can_castle_queenside = True
    castle = Move((5, 1), to_sq, is_castle=True)
    _round_trip(b, castle)
    assert b[(5, 1)] == "K" and b[rook_sq] == "R"


# ─── Promotion with and without capture ───────────────────────────────────
@pytest.mark.parametrize(
    "promo_piece,target_sq,capture",
    [
        ("Q", (7, 8), False),
        ("R", (8, 8), True),
        ("N", (7, 8), False),
        ("B", (8, 8), True),
    ],
)
def test_promotion_round_trip(promo_piece, target_sq, capture):
    pieces = {(7, 7): "P", (5, 1): "K", (5, 8): "k"}
    if capture:
        pieces[target_sq] = "r"
    b = make_board(pieces)
    move = Move((7, 7), target_sq, promo=promo_piece)
    _round_trip(b, move)
    # original pawn back, rook back if it existed
    assert b[(7, 7)] == "P"
    if capture:
        assert b[target_sq] == "r"
    else:
        assert b[target_sq] == b.EMPTY


def test_undo_capture_restores_captured_piece():
    b = make_board({(5, 5): "P", (5, 6): "p"})
    m = Move((5, 5), (5, 6))
    rights = b.make_move(m)
    b.undo_move(m, rights)
    assert b[(5, 5)] == "P" and b[(5, 6)] == "p"


@pytest.mark.parametrize("piece", ["Q", "R", "B", "N"])
def test_promotion_with_capture_and_underpromotion(piece):
    b = make_board({(7, 7): "P", (8, 8): "r"})
    promo = Move((7, 7), (8, 8), promo=piece)
    rights = b.make_move(promo)
    b.undo_move(promo, rights)
    assert b[(7, 7)] == "P" and b[(8, 8)] == "r"


@pytest.mark.parametrize("rook_sq,to_sq", [((8, 1), (7, 1)), ((1, 1), (3, 1))])
def test_castling_make_undo_round_trip(rook_sq, to_sq):
    b = make_board({(5, 1): "K", rook_sq: "R", (5, 8): "k"})
    if rook_sq[0] == 8:
        b.white_can_castle_kingside = True
    else:
        b.white_can_castle_queenside = True
    castle = Move((5, 1), to_sq, is_castle=True)
    _round_trip(b, castle)
    # After undo, original placement must be restored
    assert b[(5, 1)] == "K" and b[rook_sq] == "R"


def test_rook_move_rights_toggle_and_restore():
    # Start with both rights; move a1-a2, then undo
    b = make_board({(5, 1): "K", (1, 1): "R", (5, 8): "k"})
    b.white_can_castle_queenside = True
    move = Move((1, 1), (1, 2))
    rights_before = (b.white_can_castle_kingside, b.white_can_castle_queenside)

    undodata = b.make_move(move)
    assert (
        not b.white_can_castle_queenside
    ), "Rook move must clear queenside right"

    b.undo_move(move, undodata)
    assert (
        b.white_can_castle_kingside,
        b.white_can_castle_queenside,
    ) == rights_before, "Undo must restore original castling rights"


def test_undo_white_en_passant_round_trip():
    # Black pawn plays ...e7-e5; white d5×e6 ep
    b = make_board({(4, 5): "P", (5, 7): "p", (5, 8): "k", (5, 1): "K"})
    dbl = Move((5, 7), (5, 5))  # ...e7→e5
    b.make_move(dbl)
    b.en_passant = (5, 6)

    ep = Move((4, 5), (5, 6), is_en_passant=True)
    rights = b.make_move(ep)
    b.undo_move(ep, rights)

    assert b[(4, 5)] == "P" and b[(5, 6)] == b.EMPTY and b[(5, 5)] == "p"
