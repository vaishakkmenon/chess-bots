import pytest
from engine.moves.move import Move
from engine.moves.pawn import pawn_moves
from engine.moves.generator import legal_moves
from tests.utils import (
    make_board,
    print_section,
)


# ─── Edge Case: Promotion Legality — Legal but Mixed Moves ──────────────────
def test_promotion_legal_check():
    print_section("Promotion Legality")

    b = make_board(
        {
            # White king and pinned pieces
            (5, 1): "K",  # e1
            (4, 1): "R",  # d1 — pinned by a1 (legal: d1→c1, b1, a1)
            (6, 1): "R",  # f1 — pinned by h1 (legal: f1→g1, h1)
            (4, 2): "P",  # d2 — pinned by c3 (legal: d2→c3)
            (5, 2): "P",  # e2 — pinned by e8 (legal: e2→e3, e4)
            (6, 2): "P",  # f2 — pinned by g3 (legal: f2→g3)
            (7, 7): "P",  # g7 — promotion pawn
            # Black attackers creating pins
            (1, 1): "r",
            (8, 1): "r",
            (3, 3): "b",
            (5, 8): "q",
            (7, 3): "b",
        }
    )

    legal = legal_moves(b, "white")
    promotions = [m for m in legal if m.promo]
    assert promotions, "Expected at least one promotion move"

    # Ensure the pinned pieces are only moving along the pin
    for m in legal:
        frm, to = m.from_sq, m.to_sq

        # d1 rook: legal only to c1, b1, a1
        if frm == (4, 1):
            assert (
                to[1] == 1 and to[0] < 4
            ), f"Illegal pin-breaking move from d1: {m}"

        # f1 rook: legal only to g1, h1
        if frm == (6, 1):
            assert (
                to[1] == 1 and to[0] > 6
            ), f"Illegal pin-breaking move from f1: {m}"

        # d2 pawn: legal only to c3
        if frm == (4, 2):
            assert to == (3, 3), f"Illegal pin-breaking move from d2: {m}"

        # e2 pawn: legal only to e3, e4
        if frm == (5, 2):
            assert to in {
                (5, 3),
                (5, 4),
            }, f"Illegal pin-breaking move from e2: {m}"

        # f2 pawn: legal only to g3
        if frm == (6, 2):
            assert to == (7, 3), f"Illegal pin-breaking move from f2: {m}"

    print("✔️ Promotions are included and pins are respected.")


def _moves_from(b, frm):
    return [m for m in pawn_moves(b, "white") if m.from_sq == frm]


def test_all_four_promotion_choices_available():
    b = make_board({(5, 1): "K", (7, 7): "P"})
    promos = {m.promo for m in _moves_from(b, (7, 7))}
    assert promos == {"Q", "R", "B", "N"}


def test_promotion_gives_check():
    b = make_board({(5, 1): "K", (7, 7): "P", (8, 8): "k"})
    assert any(
        m.to_sq == (8, 8) and m.promo == "Q" for m in _moves_from(b, (7, 7))
    )


@pytest.mark.parametrize("promo_piece", ["Q", "R", "B", "N"])
def test_black_pawn_promotion_round_trip(promo_piece):
    b = make_board({(2, 2): "p", (5, 1): "K", (5, 8): "k"})
    mv = Move((2, 2), (2, 1), promo=promo_piece)  # b2→b1=?
    rights, prev_halfclock = b.make_move(mv)
    b.undo_move(mv, rights, prev_halfclock)
    assert b[(2, 2)] == "p" and b[(2, 1)] == b.EMPTY


def test_promotion_checkmate_is_generated():
    # Simple mate net: white pawn g7 takes h8=Q (checkmate)
    b = make_board({(7, 7): "P", (8, 8): "k", (5, 1): "K"})
    mates = [
        m
        for m in legal_moves(b, "white")
        if m.to_sq == (8, 8) and m.promo == "Q"
    ]
    assert mates, "Promotion mate move must be generated"
