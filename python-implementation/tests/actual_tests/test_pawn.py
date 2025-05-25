from engine.moves.move import Move
from engine.moves.pawn import pawn_moves
from engine.moves.generator import legal_moves
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
    rights, prev_halfclock = b.make_move(move)
    ep_moves = pawn_moves(b, "white")
    assert_true(
        any(is_en_passant(m, (4, 6)) for m in ep_moves),
        "Must include en passant",
    )
    b.undo_move(move, rights, prev_halfclock)


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
    rights, prev_halfclock = b.make_move(move)
    ep_moves = pawn_moves(b, "black")
    assert_true(
        any(is_en_passant(m, (6, 3)) for m in ep_moves),
        "Black must include en passant capture to f3",
    )
    b.undo_move(move, rights, prev_halfclock)


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
    rights1, prev_halfclock1 = b.make_move(move1)
    move2 = Move((1, 1), (1, 2))  # White rook moves
    rights2, prev_halfclock2 = b.make_move(move2)
    ep_moves = pawn_moves(b, "white")
    assert_true(
        all(not m.is_en_passant for m in ep_moves),
        "En passant should expire after a non-pawn move",
    )
    b.undo_move(move2, rights2, prev_halfclock2)
    b.undo_move(move1, rights1, prev_halfclock1)


def _dests(b, frm):
    return {m.to_sq for m in pawn_moves(b, "white") if m.from_sq == frm}


def test_pawn_blocked_single_and_double_push():
    b = make_board({(5, 1): "K", (5, 2): "P", (5, 3): "N"})
    assert _dests(b, (5, 2)) == set()


def test_pawn_blocked_double_only_push():
    b = make_board({(5, 1): "K", (5, 2): "P", (5, 4): "n"})
    assert _dests(b, (5, 2)) == {(5, 3)}


def test_pawn_no_double_after_moving():
    b = make_board({(5, 1): "K", (5, 3): "P"})
    assert (5, 5) not in _dests(b, (5, 3))


def test_en_passant_illegal_if_exposes_king():
    b = make_board({(5, 1): "K", (5, 5): "P", (6, 5): "p", (5, 8): "r"})
    b.en_passant_target = (6, 6)
    # White pawn on e5 appears able to capture d5 en‑passant, but doing so
    # would expose the white king to the rook on e8
    # so the move must be filtered.
    assert not any(
        getattr(m, "is_en_passant", False) for m in legal_moves(b, "white")
    )


def test_pawn_promotion_capture_check_present():
    b = make_board({(5, 1): "K", (7, 7): "P", (8, 8): "k"})
    dests = _dests(b, (7, 7))
    assert (8, 8) in dests


def test_pawn_no_backwards_moves():
    b = make_board({(5, 4): "P"})
    assert all(m.to_sq[1] > 4 for m in pawn_moves(b, (5, 4)))


def test_pawn_en_passant_right_capture():
    # King on e1 for legality context
    b = make_board(
        {(5, 1): "K", (5, 5): "P", (6, 7): "p"}
    )  # White pawn e5, Black pawn f7
    move = Move((6, 7), (6, 5))  # ...f7–f5
    rights, prev_halfclock = b.make_move(move)
    ep_moves = pawn_moves(b, "white")
    assert any(
        is_en_passant(m, (6, 6)) for m in ep_moves
    )  # e5 × f6 en-passant exists
    b.undo_move(move, rights, prev_halfclock)


def test_black_pawn_en_passant_left_capture():
    # king e1, black pawn f4, white pawn e2
    b = make_board({(5, 1): "K", (6, 4): "p", (5, 2): "P"})
    move = Move((5, 2), (5, 4))  # e2→e4
    rights, prev_halfclock = b.make_move(move)
    ep_moves = pawn_moves(b, "black")
    assert any(
        is_en_passant(m, (5, 3)) for m in ep_moves
    ), "Black must include en-passant capture to e3"
    b.undo_move(move, rights, prev_halfclock)


def test_pawn_cannot_move_when_pinned_diagonal():
    # pin line: b4–c3–d2–e1
    b = make_board({(5, 1): "K", (4, 2): "P", (2, 4): "b"})
    assert all(
        m.from_sq != (4, 2) for m in legal_moves(b, "white")
    ), "Pawn on d2 is pinned and must not be allowed to move"


def test_pawn_promotion_capture_all_choices():
    b = make_board(
        {(5, 1): "K", (7, 7): "P", (8, 8): "r"}
    )  # White pawn g7 can capture h8
    moves = [m for m in pawn_moves(b, "white") if m.to_sq == (8, 8)]
    promos = {m.promo for m in moves}
    assert_equal(
        promos, {"Q", "R", "B", "N"}, "All four promotion options required"
    )
