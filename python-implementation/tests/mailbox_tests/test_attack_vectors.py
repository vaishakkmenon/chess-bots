from engine.mailbox.moves.helpers import is_square_attacked
from engine.mailbox.moves.generator import legal_moves
from tests.utils import (
    make_board,
    assert_equal,
    print_section,
)

ATTACK_TESTS = [
    # ─── Pawn attacks ────────────────────────────────────────────────────────
    ("white pawn e5→d6", {(5, 5): "P"}, (4, 6), "white", True),
    ("white pawn e5→f6", {(5, 5): "P"}, (6, 6), "white", True),
    ("white pawn e5 no→e6", {(5, 5): "P"}, (5, 6), "white", False),
    ("black pawn e4→d3", {(5, 4): "p"}, (4, 3), "black", True),
    ("black pawn e4→f3", {(5, 4): "p"}, (6, 3), "black", True),
    ("black pawn e4 no→e3", {(5, 4): "p"}, (5, 3), "black", False),
    # ─── Knight attacks ──────────────────────────────────────────────────────
    ("white knight e4→g5", {(5, 4): "N"}, (7, 5), "white", True),
    ("white knight e4→f2", {(5, 4): "N"}, (6, 2), "white", True),
    ("white knight e4 no→e5", {(5, 4): "N"}, (5, 5), "white", False),
    ("black knight d5→b6", {(4, 5): "n"}, (2, 6), "black", True),
    ("black knight d5→e7", {(4, 5): "n"}, (5, 7), "black", True),
    ("black knight d5 no→d6", {(4, 5): "n"}, (4, 6), "black", False),
    # ─── Bishop/Queen diagonal attacks ───────────────────────────────────────
    ("white bishop c1→a3", {(3, 1): "B"}, (1, 3), "white", True),
    ("white bishop f4→b8", {(6, 4): "B"}, (2, 8), "white", True),
    (
        "white bishop blocked by knight",
        {(4, 4): "B", (6, 6): "N"},
        (7, 7),
        "white",
        False,
    ),
    ("black queen c8→f5 diag", {(3, 8): "q"}, (6, 5), "black", True),
    (
        "black queen blocked diag",
        {(3, 8): "q", (5, 6): "p"},
        (7, 4),
        "black",
        False,
    ),
    # ─── Rook/Queen orthogonal attacks ───────────────────────────────────────
    ("white rook d4→d7", {(4, 4): "R"}, (4, 7), "white", True),
    ("white rook a1→d1", {(1, 1): "R"}, (4, 1), "white", True),
    (
        "white rook blocked orth",
        {(4, 4): "R", (4, 6): "P"},
        (4, 8),
        "white",
        False,
    ),
    ("black queen h8→h5 orth", {(8, 8): "q"}, (8, 5), "black", True),
    (
        "black queen blocked orth",
        {(8, 8): "q", (8, 6): "P"},
        (8, 4),
        "black",
        False,
    ),
    # ─── King adjacency ──────────────────────────────────────────────────────
    ("white king e4→d5", {(5, 4): "K"}, (4, 5), "white", True),
    ("white king e4→e3", {(5, 4): "K"}, (5, 3), "white", True),
    ("white king e4 no→g6", {(5, 4): "K"}, (7, 6), "white", False),
    ("black king a8→b8", {(1, 8): "k"}, (2, 8), "black", True),
    ("black king h1→g1", {(8, 1): "k"}, (7, 1), "black", True),
    ("black king h1 no→f1", {(8, 1): "k"}, (6, 1), "black", False),
]


def test_all_attack_vectors():
    print_section("Piece Attack Tests")
    for desc, setup, sq, color, expected in ATTACK_TESTS:
        b = make_board(setup)
        result = is_square_attacked(b, sq, color)
        assert_equal(
            result, expected, f"{desc} — expected {expected}, got {result}"
        )
    print("✔️ All attack-vector tests passed.")


def test_attack_wrong_colour_returns_false():
    b = make_board({(4, 4): "R"})  # white rook d4 attacks d7
    assert not is_square_attacked(b, (4, 7), "black")


def test_rook_attack_stops_before_second_enemy():
    b = make_board(
        {(4, 4): "R", (4, 6): "p", (4, 8): "p"}
    )  # rook d4, pawns d6 & d8
    assert is_square_attacked(b, (4, 6), "white")
    assert not is_square_attacked(b, (4, 8), "white")


def test_king_cannot_move_adjacent_to_enemy_king():
    # White king e2 (5,2), Black king e4 (5,4)
    b = make_board({(5, 2): "K", (5, 4): "k"})
    king_moves_from_e2 = {
        m.to_sq for m in legal_moves(b, "white") if m.from_sq == (5, 2)
    }

    # Any of these squares would leave the kings touching
    forbidden = {(5, 3), (4, 3), (6, 3)}  # e3, d3, f3

    # Engine must exclude them
    assert forbidden.isdisjoint(
        king_moves_from_e2
    ), "King must not step adjacent to opposing king"
