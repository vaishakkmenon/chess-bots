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
