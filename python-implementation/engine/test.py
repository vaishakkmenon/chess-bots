# engine/test_pieces.py

# flake8: noqa: E402
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from engine.board import Board
from engine.rules import in_check
from engine.moves.move import Move
from engine.moves.pawn import pawn_moves
from engine.moves.knight import knight_moves
from engine.moves.bishop import bishop_moves
from engine.moves.rook import rook_moves
from engine.moves.queen import queen_moves
from engine.moves.king import king_moves
from engine.moves.helpers import is_square_attacked
from engine.moves.generator import legal_moves

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

    b = make_board({(5, 1): "K"})
    b.white_can_castle_kingside = True
    b.white_can_castle_queenside = True
    m = Move((5, 1), (5, 2))
    rights = b.make_move(m)
    assert not b.white_can_castle_kingside
    assert not b.white_can_castle_queenside
    b.undo_move(m, rights)

    b = make_board({(1, 1): "R"})
    b.white_can_castle_queenside = True
    m = Move((1, 1), (1, 2))
    rights = b.make_move(m)
    assert not b.white_can_castle_queenside
    b.undo_move(m, rights)

    b = make_board({(8, 1): "R"})
    b.white_can_castle_kingside = True
    m = Move((8, 1), (8, 2))
    rights = b.make_move(m)
    assert not b.white_can_castle_kingside
    b.undo_move(m, rights)

    b = make_board({(1, 1): "R", (2, 1): "p"})
    b.white_can_castle_queenside = True
    m = Move((2, 1), (1, 1))
    rights = b.make_move(m)
    assert not b.white_can_castle_queenside
    b.undo_move(m, rights)

    b = make_board({(8, 1): "R", (7, 1): "p"})
    b.white_can_castle_kingside = True
    m = Move((7, 1), (8, 1))
    rights = b.make_move(m)
    assert not b.white_can_castle_kingside
    b.undo_move(m, rights)

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


def test_legal_moves_filter():
    print_section("Legal Moves Filter")

    # Setup: white king on e1, black rook attacking from e8
    b = make_board({(5, 1): "K", (5, 8): "r"})  # e1 and e8
    legal = legal_moves(b, "white")

    expected = {(4, 1), (4, 2), (6, 1), (6, 2)}
    actual = {m.to_sq for m in legal}
    assert (
        actual == expected
    ), f"Expected king escape squares {expected}, got {actual}"

    # Now test that king has an escape
    b = make_board({(5, 1): "K", (5, 8): "r", (4, 1): "."})  # d1 is empty
    legal = legal_moves(b, "white")
    squares = [m.to_sq for m in legal]
    assert (
        4,
        1,
    ) in squares, "King should be able to move to d1 to escape check"

    print("✔️ Legal move filtering based on check works.")


# ─── Edge Case: Pinned Piece Cannot Move ─────────────────────────────────────
def test_pinned_piece_cannot_move():
    print_section("Pinned Piece Test")

    # White bishop pinned along e-file by black rook; moving it exposes king
    b = make_board(
        {
            (5, 1): "K",  # e1
            (5, 2): "B",  # e2
            (5, 8): "r",  # e8
        }
    )
    legal = legal_moves(b, "white")
    assert all(
        m.from_sq != (5, 2) for m in legal
    ), "Pinned bishop must not be allowed to move"
    print("✔️ Pinned piece is restricted properly.")


# ─── Edge Case: En Passant Leaves King in Check ─────────────────────────────
def test_en_passant_exposes_check():
    print_section("En Passant Exposes Check")

    # En passant would expose king to attack from black rook
    b = make_board(
        {
            (5, 5): "P",  # e5
            (6, 5): "p",  # f5
            (5, 1): "K",  # e1
            (5, 8): "r",  # e8 (attacking down the file if e5 is cleared)
        }
    )
    move = Move((6, 7), (6, 5))  # Black pawn double move: f7→f5
    b.make_move(move)

    ep_moves = legal_moves(b, "white")
    assert all(
        not m.is_en_passant for m in ep_moves
    ), "En passant that reveals check must be illegal"
    print("✔️ En passant exposing king is blocked.")


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


# ─── Edge Case: Undo Promotion Restores Pawn ─────────────────────────────────
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


# ─── Edge Case: Double Check Only Allows King Move ───────────────────────────
def test_double_check_only_king_moves():
    print_section("Double Check Test")

    b = make_board(
        {
            (5, 1): "K",  # e1
            (4, 2): "r",  # d2
            (6, 2): "b",  # f2
        }
    )
    legal = legal_moves(b, "white")
    assert all(
        m.from_sq == (5, 1) for m in legal
    ), "Only king may move under double check"
    print("✔️ Only king moves allowed during double check.")


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
    test_make_and_undo()
    test_legal_moves_filter()
    test_pinned_piece_cannot_move()
    test_en_passant_exposes_check()
    test_promotion_legal_check()
    test_undo_promotion()
    test_double_check_only_king_moves()
    print("\n ✔️ All tests passed!")
