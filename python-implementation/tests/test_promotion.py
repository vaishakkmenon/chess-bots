import pytest
from engine.moves.generator import legal_moves
from tests.utils import (
    make_board,
    print_section,
)


def make_complex_board():
    return make_board(
        {
            (5, 1): "K",  # White king
            (4, 1): "R",  # d1 rook (pinned)
            (6, 1): "R",  # f1 rook (pinned)
            (4, 2): "P",  # d2 pawn (pinned)
            (5, 2): "P",  # e2 pawn (pinned)
            (6, 2): "P",  # f2 pawn (pinned)
            (7, 7): "P",  # **g7 pawn ready to promote**
            # Black pieces creating the pins
            (1, 1): "r",
            (8, 1): "r",
            (3, 3): "b",
            (7, 3): "b",
            (5, 8): "q",
        }
    )


def test_promotion_exists():
    print_section("Test Promotion Exists")
    legal = legal_moves(make_complex_board(), "white")
    assert any(m.promo for m in legal)


@pytest.mark.parametrize(
    "frm, allowed",
    [
        ((4, 1), {(3, 1), (2, 1), (1, 1)}),  # rook d1
        ((6, 1), {(7, 1), (8, 1)}),  # rook f1
        ((4, 2), {(3, 3)}),  # pawn d2
        ((5, 2), {(5, 3), (5, 4)}),  # pawn e2
        ((6, 2), {(7, 3)}),  # pawn f2
    ],
)
def test_pinned_piece_moves_along_pin(frm, allowed):
    print_section("Test Pinned Pieces")
    legal = legal_moves(make_complex_board(), "white")
    moves = {m.to_sq for m in legal if m.from_sq == frm}
    assert moves <= allowed
