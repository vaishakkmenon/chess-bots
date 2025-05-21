# engine/test_pieces.py

from board import Board
from rules import in_check
from moves.move import Move
from moves.pawn import pawn_moves
from moves.knight import knight_moves
from moves.bishop import bishop_moves
from moves.rook import rook_moves
from moves.queen import queen_moves
from moves.king import king_moves
from moves.helpers import is_square_attacked

# Each tuple is:
# (description, piece placement, test square, attacking color, expected)
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
        "white bishop blocked by pawn",
        {(4, 4): "B", (6, 6): "P"},
        (7, 7),
        "white",
        True,
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


def assert_equal(a, b, msg=""):
    if a != b:
        raise AssertionError(f"{msg} — expected {b}, got {a}")


def assert_true(expr, msg=""):
    if not expr:
        raise AssertionError(f"{msg}")


def make_board(pieces: dict[tuple[int, int], str]) -> Board:
    b = Board()
    b.squares = [[b.EMPTY for _ in range(8)] for _ in range(8)]
    for (f, r), char in pieces.items():
        b[(f, r)] = char
    return b


def print_section(title: str):
    print(f"\n{'='*10} {title} {'='*10}")


def print_board(b: Board):
    print(b)


# ─── Helpers to classify pawn moves ──────────────────────────────────────────
def is_single_push(move: Move) -> bool:
    f0, r0 = move.from_sq
    f1, r1 = move.to_sq
    return move.promo is None and f0 == f1 and r1 == r0 + 1


def is_double_push(move: Move) -> bool:
    f0, r0 = move.from_sq
    f1, r1 = move.to_sq
    return move.promo is None and f0 == f1 and r1 == r0 + 2


def is_capture(move: Move) -> bool:
    f0, r0 = move.from_sq
    f1, r1 = move.to_sq
    return move.promo is None and abs(f1 - f0) == 1 and r1 == r0 + 1


def is_en_passant(move: Move, ep_target: tuple[int, int]) -> bool:
    return move.is_en_passant and move.to_sq == ep_target


def is_promotion(move: Move) -> bool:
    return move.promo in {"Q", "R", "B", "N"}


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
    b.make_move((4, 7), (4, 5), None)  # d7→d5
    ep_moves = pawn_moves(b, "white")
    # en passant target square is d6 = (4,6)
    assert_true(
        any(is_en_passant(m, (4, 6)) for m in ep_moves),
        "Must include en passant",
    )

    # 4) promotions
    b = make_board({(7, 7): "P"})
    pr = pawn_moves(b, "white")
    promos = {m.promo for m in pr if is_promotion(m)}
    assert_equal(
        promos, {"Q", "R", "B", "N"}, "Promotion must offer all four choices"
    )

    print("✔️ All pawn‐move categories present.")


# ─── Knight Tests ───────────────────────────────────────────────────────────
def test_knight_moves():
    print_section("Knight Moves Tests")

    # center quiet & capture in one set
    b = make_board({(4, 4): "N", (6, 5): "p"})
    km = knight_moves(b, "white")
    # quiet moves = jumps to empty squares
    quiet = [m for m in km if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in km if b[m.to_sq].islower()]
    assert_true(
        len(quiet) > 0, "Knight must have at least one non-capture jump"
    )
    assert_true(
        len(captures) > 0, "Knight must have at least one capture jump"
    )

    print("✔️ Knight moves include both quiet and capture.")


# ─── Bishop Tests ────────────────────────────────────────────────────────────
def test_bishop_moves():
    print_section("Bishop Moves Tests")

    # 1) quiet + capture from center
    b = make_board({(4, 4): "B", (2, 2): "p"})
    bm = bishop_moves(b, "white")
    quiet = [m for m in bm if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in bm if b[m.to_sq].islower()]
    assert_true(len(quiet) > 0, "Bishop must have at least one diagonal quiet")
    assert_true(
        len(captures) > 0, "Bishop must have at least one diagonal capture"
    )

    # 2) blocked by friend
    b = make_board({(4, 4): "B", (6, 6): "P"})
    bm = bishop_moves(b, "white")
    # should NOT include any move landing on (7,7) or beyond
    assert_true(
        all(m.to_sq != (7, 7) for m in bm),
        "Bishop must stop before a friendly pawn at (6,6)",
    )

    # 3) edge-of-board no wrap
    b = make_board({(1, 1): "B"})
    bm = bishop_moves(b, "white")
    # only NE direction should produce moves (to 2,2 .. 8,8)
    expected = {(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)}
    seen = {m.to_sq for m in bm}
    assert_equal(
        seen,
        expected - {(1, 1)},
        "Bishop at a1 must slide along one diagonal only",
    )

    print("✔️ Bishop slides pass quiet, capture, block & edge tests.")


# ─── Rook Tests ──────────────────────────────────────────────────────────────
def test_rook_moves():
    print_section("Rook Moves Tests")

    # 1) quiet + capture from center
    b = make_board({(4, 4): "R", (4, 7): "p"})
    rm = rook_moves(b, "white")
    quiet = [m for m in rm if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in rm if b[m.to_sq].islower()]
    assert_true(len(quiet) > 0, "Rook must have at least one file/rank quiet")
    assert_true(
        len(captures) > 0, "Rook must have at least one file/rank capture"
    )

    # 2) blocked by friend
    b = make_board({(4, 4): "R", (4, 2): "P"})
    rm = rook_moves(b, "white")
    # should NOT include any move to (4,1)
    assert_true(
        all(m.to_sq != (4, 1) for m in rm),
        "Rook must stop before a friendly pawn at (4,2)",
    )

    # 3) edge-of-board no wrap
    b = make_board({(8, 8): "R"})
    rm = rook_moves(b, "white")
    # only W and S directions: ranks 1–8 at file=8 and files 1–8 at rank=8
    expected = {(i, 8) for i in range(1, 9)} | {(8, i) for i in range(1, 9)}
    seen = {m.to_sq for m in rm}
    # remove starting square:
    assert_equal(
        seen,
        expected - {(8, 8)},
        "Rook at h8 must slide along file h and rank 8 only",
    )

    print("✔️ Rook slides pass quiet, capture, block & edge tests.")


# ─── Queen Tests ─────────────────────────────────────────────────────────────
def test_queen_moves():
    print_section("Queen Moves Tests")

    # 1) quiet + capture from center
    b = make_board({(4, 4): "Q", (4, 7): "p", (7, 4): "p"})
    qm = queen_moves(b, "white")
    quiet = [m for m in qm if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in qm if b[m.to_sq].islower()]
    assert_true(len(quiet) > 0, "Queen must have at least one quiet slide")
    assert_true(
        len(captures) > 0, "Queen must have at least one capture slide"
    )

    # 2) diagonal block by friend (use a pawn so only one queen is tested)
    b = make_board({(4, 4): "Q", (6, 6): "P"})
    qm = queen_moves(b, "white")
    # only slides up to (5,5), but not (6,6) or beyond
    assert_true(
        all(m.to_sq != (7, 7) for m in qm),
        "Queen must stop before friendly pawn on diagonal",
    )

    # 3) file/rank block by friend (use a pawn)
    b = make_board({(4, 4): "Q", (4, 2): "P"})
    qm = queen_moves(b, "white")
    # only slides down to (4,3), but not (4,2) or (4,1)
    file_moves = [m.to_sq for m in qm if m.from_sq == (4, 4)]
    assert_true(
        all(t != (4, 1) for t in file_moves),
        "Queen must stop before friendly pawn on file",
    )

    # 4) edge-of-board no wrap
    b = make_board({(1, 8): "Q"})
    qm = queen_moves(b, "white")
    seen = {m.to_sq for m in qm}
    assert_true(
        all(1 <= f <= 8 and 1 <= r <= 8 for (f, r) in seen),
        "All queen moves must stay on-board",
    )

    print("✔️ Queen slides pass quiet, capture, block & edge tests.")


# ─── King Tests ──────────────────────────────────────────────────────────────
def test_king_moves():
    print_section("King Basic Moves")

    # King in center with one enemy
    b = make_board({(4, 4): "K", (5, 5): "p"})
    # manually disable castling for now
    b.white_can_castle_kingside = False
    b.white_can_castle_queenside = False

    km = king_moves(b, "white")
    quiet = [m for m in km if b[m.to_sq] == Board.EMPTY]
    captures = [m for m in km if b[m.to_sq].islower()]

    assert_true(
        len(quiet) == 7,
        "King on an empty 8x8 minus one enemy should have 7 quiet",
    )
    assert_true(
        len(captures) == 1,
        "King must be able to capture the one enemy at (5,5)",
    )

    print("✔️ King basic quiet + capture moves pass.")


def test_all_attack_vectors():
    print_section("Piece Attack Tests")
    for desc, setup, sq, color, expected in ATTACK_TESTS:
        b = make_board(setup)
        result = is_square_attacked(b, sq, color)
        assert_equal(
            result, expected, f"{desc} — expected {expected}, got {result}"
        )
    print("✔️ All attack-vector tests passed.")


def test_king_castling():
    print_section("King Castling Tests")

    # ——— Kingside allowed ———
    b = make_board({(5, 1): "K", (8, 1): "R"})
    b.white_can_castle_kingside = True
    km = king_moves(b, "white")
    assert_true(
        any(
            m.from_sq == (5, 1) and m.to_sq == (7, 1) and m.is_castle
            for m in km
        ),
        "Must allow kingside castling when all conditions met",
    )

    # ——— Queenside allowed ———
    b = make_board({(5, 1): "K", (1, 1): "R"})
    b.white_can_castle_queenside = True
    km = king_moves(b, "white")
    assert_true(
        any(
            m.from_sq == (5, 1) and m.to_sq == (3, 1) and m.is_castle
            for m in km
        ),
        "Must allow queenside castling when all conditions met",
    )

    # ——— Blocked kingside ———
    b = make_board({(5, 1): "K", (6, 1): "P", (8, 1): "R"})
    b.white_can_castle_kingside = True
    km = king_moves(b, "white")
    assert_true(
        not any(
            m.from_sq == (5, 1) and m.to_sq == (7, 1) and m.is_castle
            for m in km
        ),
        "Must NOT allow kingside castling if path blocked",
    )

    # ——— King in check ———
    b = make_board(
        {(5, 1): "K", (8, 1): "R", (5, 8): "q"}
    )  # Black queen aiming at king
    b.white_can_castle_kingside = True
    km = king_moves(b, "white")
    assert_true(
        not any(
            m.from_sq == (5, 1) and m.to_sq == (7, 1) and m.is_castle
            for m in km
        ),
        "Must NOT allow castling while king is in check",
    )

    # ——— Square passed through is attacked ———
    b = make_board({(5, 1): "K", (8, 1): "R", (6, 8): "q"})  # Attacks f1
    b.white_can_castle_kingside = True
    km = king_moves(b, "white")
    assert_true(
        not any(
            m.from_sq == (5, 1) and m.to_sq == (7, 1) and m.is_castle
            for m in km
        ),
        "Must NOT allow castling if square passed through is attacked",
    )

    # ——— King not on home square ———
    b = make_board({(4, 1): "K", (8, 1): "R"})
    b.white_can_castle_kingside = True
    km = king_moves(b, "white")
    assert_true(
        not any(
            m.from_sq == (4, 1) and m.to_sq == (6, 1) and m.is_castle
            for m in km
        ),
        "Must NOT allow castling if king is not on e1",
    )

    print("✔️ Castling tests passed.")


def test_castling_rights():
    print_section("Castling Rights Flags")

    # ─── King moves: should clear both sides ───
    b = make_board({(5, 1): "K"})
    b.white_can_castle_kingside = True
    b.white_can_castle_queenside = True
    b.make_move((5, 1), (5, 2))
    assert (
        not b.white_can_castle_kingside
    ), "King move must clear kingside castling"
    assert (
        not b.white_can_castle_queenside
    ), "King move must clear queenside castling"

    # ─── Rook move: a1 → a2 should clear queenside ───
    b = make_board({(1, 1): "R"})
    b.white_can_castle_queenside = True
    b.make_move((1, 1), (1, 2))
    assert (
        not b.white_can_castle_queenside
    ), "Rook move from a1 must clear queenside right"

    # ─── Rook move: h1 → h2 should clear kingside ───
    b = make_board({(8, 1): "R"})
    b.white_can_castle_kingside = True
    b.make_move((8, 1), (8, 2))
    assert (
        not b.white_can_castle_kingside
    ), "Rook move from h1 must clear kingside right"

    # ─── Rook capture: a1 rook is captured ───
    b = make_board({(1, 1): "R", (2, 1): "p"})
    b.white_can_castle_queenside = True
    b.make_move((2, 1), (1, 1))
    assert (
        not b.white_can_castle_queenside
    ), "Captured rook on a1 must clear queenside right"

    # ─── Rook capture: h1 rook is captured ───
    b = make_board({(8, 1): "R", (7, 1): "p"})
    b.white_can_castle_kingside = True
    b.make_move((7, 1), (8, 1))
    assert (
        not b.white_can_castle_kingside
    ), "Captured rook on h1 must clear kingside right"

    print("✔️ Castling rights flags correctly updated.")


def test_in_check():
    print_section("Check Detection")

    # White king in check from black queen
    b = make_board({(5, 1): "K", (5, 8): "q"})
    assert in_check(b, "white"), "White should be in check from e8 queen"

    # Black king not in check
    b = make_board({(5, 8): "k"})
    assert not in_check(b, "black"), "Black king alone should not be in check"

    print("✔️ in_check() correctly detects check state.")


if __name__ == "__main__":
    test_pawn_moves()
    test_knight_moves()
    test_bishop_moves()
    test_rook_moves()
    test_queen_moves()
    test_king_moves()
    test_king_castling()
    test_all_attack_vectors()
    test_castling_rights()
    test_in_check()
    print("\n ✔️ All tests passed!")
