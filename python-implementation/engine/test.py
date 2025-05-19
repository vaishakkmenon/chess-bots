# engine/test_pieces.py

from board import Board
from moves.pawn import pawn_moves
from moves.knight import knight_moves
from moves.bishop import bishop_moves


def assert_equal(a, b, msg=""):
    if a != b:
        raise AssertionError(f"{msg} — expected {b}, got {a}")


def assert_true(expr, msg=""):
    if not expr:
        raise AssertionError(f"{msg}")


def make_board(pieces: dict[tuple[int, int], str]) -> Board:
    b = Board()
    for (f, r), char in pieces.items():
        b[(f, r)] = char
    return b


def print_section(title: str):
    print(f"\n{'='*10} {title} {'='*10}")


def print_board(b: Board):
    print(b)


# ─── Helpers to classify pawn moves ──────────────────────────────────────────
def is_single_push(move):
    (f0, r0), (f1, r1), promo = move
    return promo is None and f0 == f1 and r1 == r0 + 1


def is_double_push(move):
    (f0, r0), (f1, r1), promo = move
    return promo is None and f0 == f1 and r1 == r0 + 2


def is_capture(move):
    (f0, r0), (f1, r1), promo = move
    return promo is None and abs(f1 - f0) == 1 and r1 == r0 + 1


def is_en_passant(move, ep_target):
    # ep_target is the square behind a double-pushed pawn
    return is_capture(move) and move[1] == ep_target


def is_promotion(move):
    return move[2] in {"Q", "R", "B", "N"}


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
    promos = {m[2] for m in pr if is_promotion(m)}
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
    quiet = [(s, t, p) for (s, t, p) in km if b[t] == Board.EMPTY]
    captures = [(s, t, p) for (s, t, p) in km if b[t].islower()]
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

    # center quiet & capture
    b = make_board({(4, 4): "B", (2, 2): "p"})
    bm = bishop_moves(b, "white")
    quiet = [(s, t, p) for (s, t, p) in bm if b[t] == Board.EMPTY]
    captures = [(s, t, p) for (s, t, p) in bm if b[t].islower()]
    assert_true(
        len(quiet) > 0, "Bishop must have at least one non-capture diagonal"
    )
    assert_true(
        len(captures) > 0, "Bishop must have at least one capture diagonal"
    )

    print("✔️ Bishop moves include both quiet and capture.")


if __name__ == "__main__":
    test_pawn_moves()
    test_knight_moves()
    test_bishop_moves()
    print("\n✔️ All piece-specific tests passed!")
