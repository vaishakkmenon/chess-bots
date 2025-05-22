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


def test_pawn_pushes():
    print_section("Pawn Push Tests")
    b = make_board({(2, 2): "P"})
    pm = pawn_moves(b, "white")
    assert_true(
        any(is_single_push(m, "white") for m in pm),
        "Must have at least one single push",
    )
    assert_true(
        any(is_double_push(m, "white") for m in pm),
        "Must have at least one double push",
    )


def test_pawn_capture():
    print_section("Pawn Capture Test")
    b = make_board({(4, 4): "P", (5, 5): "p"})
    caps = pawn_moves(b, "white")
    assert_true(
        any(is_capture(m, "white") for m in caps),
        "Must include at least one capture",
    )


def test_pawn_en_passant():
    print_section("En Passant Test")
    b = make_board({(5, 5): "P", (4, 7): "p"})
    move = Move((4, 7), (4, 5))  # d7→d5
    rights = b.make_move(move)
    ep_moves = pawn_moves(b, "white")
    assert_true(
        any(is_en_passant(m, (4, 6)) for m in ep_moves),
        "Must include en passant",
    )
    b.undo_move(move, rights)


def test_pawn_promotions():
    print_section("Pawn Promotion Test")
    b = make_board({(7, 7): "P"})
    pr = pawn_moves(b, "white")
    promos = {m.promo for m in pr if is_promotion(m)}
    assert_equal(
        promos, {"Q", "R", "B", "N"}, "Promotion must offer all four choices"
    )


def test_black_pawn_pushes():
    print_section("Black Pawn Push Tests")
    b = make_board({(2, 7): "p"})
    pm = pawn_moves(b, "black")
    assert_true(
        any(is_single_push(m, "black") for m in pm),
        "Black must have at least one single push",
    )
    assert_true(
        any(is_double_push(m, "black") for m in pm),
        "Black must have at least one double push",
    )


def test_black_pawn_capture():
    print_section("Black Pawn Capture Test")
    b = make_board({(4, 5): "p", (3, 4): "P"})
    pm = pawn_moves(b, "black")
    assert_true(
        any(is_capture(m, "black") for m in pm),
        "Black must be able to capture diagonally",
    )


def test_black_pawn_en_passant():
    print_section("Black En Passant Test")
    b = make_board({(5, 4): "p", (6, 2): "P"})
    move = Move((6, 2), (6, 4))  # f2→f4
    rights = b.make_move(move)
    ep_moves = pawn_moves(b, "black")
    assert_true(
        any(is_en_passant(m, (6, 3)) for m in ep_moves),
        "Black must include en passant capture to f3",
    )
    b.undo_move(move, rights)


def test_black_pawn_promotions():
    print_section("Black Pawn Promotion Test")
    b = make_board({(2, 2): "p"})
    pr = pawn_moves(b, "black")
    promos = {m.promo for m in pr if is_promotion(m)}
    assert_equal(
        promos,
        {"Q", "R", "B", "N"},
        "Black promotion must offer all four choices",
    )


def test_en_passant_illegal_after_delay():
    print_section("En Passant Illegal After Delay")
    b = make_board({(5, 5): "P", (4, 7): "p", (1, 1): "R"})
    move1 = Move((4, 7), (4, 5))  # Black pawn double move
    b.make_move(move1)
    move2 = Move((1, 1), (1, 2))  # White rook moves
    rights = b.make_move(move2)
    ep_moves = pawn_moves(b, "white")
    assert_true(
        all(not m.is_en_passant for m in ep_moves),
        "En passant should expire after a non-pawn move",
    )
    b.undo_move(move2, rights)
    b.undo_move(move1, rights)
