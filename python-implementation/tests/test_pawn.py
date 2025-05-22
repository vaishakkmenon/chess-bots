from engine.moves.move import Move
from engine.moves.pawn import pawn_moves
from tests.utils import (
    make_board,
    assert_equal,
    assert_true,
    print_section,
    is_single_push,
    is_double_push,
    is_capture,
    is_en_passant,
    is_promotion,
)


# ─── Pawn Tests ─────────────────────────────────────────────────────────────
def test_pawn_moves():
    print_section("Pawn Moves Tests")

    # 1) single & double push from starting rank
    b = make_board({(2, 2): "P"})
    pm = pawn_moves(b, "white")
    assert_true(
        any(is_single_push(m) for m in pm),
        "Must have at least one single push",
    )
    assert_true(
        any(is_double_push(m) for m in pm),
        "Must have at least one double push",
    )

    # 2) capture
    b = make_board({(4, 4): "P", (5, 5): "p"})
    caps = pawn_moves(b, "white")
    assert_true(
        any(is_capture(m) for m in caps), "Must include at least one capture"
    )

    # 3) en passant
    b = make_board({(5, 5): "P", (4, 7): "p"})
    move = Move((4, 7), (4, 5))  # d7→d5
    rights = b.make_move(move)
    ep_moves = pawn_moves(b, "white")
    # en passant target square is d6 = (4,6)
    assert_true(
        any(is_en_passant(m, (4, 6)) for m in ep_moves),
        "Must include en passant",
    )
    b.undo_move(move, rights)

    # 4) promotions
    b = make_board({(7, 7): "P"})
    pr = pawn_moves(b, "white")
    promos = {m.promo for m in pr if is_promotion(m)}
    assert_equal(
        promos, {"Q", "R", "B", "N"}, "Promotion must offer all four choices"
    )

    print("✔️ All pawn-move categories present.")
