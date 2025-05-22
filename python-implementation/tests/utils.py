# tests/utils.py

from engine.board import Board
from engine.moves.move import Move


def make_board(pieces: dict[tuple[int, int], str]) -> Board:
    b = Board()
    b.squares = [[b.EMPTY for _ in range(8)] for _ in range(8)]
    for (f, r), char in pieces.items():
        b[(f, r)] = char
    return b


def assert_equal(a, b, msg=""):
    assert a == b, f"{msg} — expected {b}, got {a}"


def assert_true(expr, msg=""):
    assert expr, msg


def print_section(title: str):
    print(f"\n{'='*10} {title} {'='*10}")


def print_board(b: Board):
    print(b)


# ─── Pawn Move Classifiers ───────────────────────────────────────────────────


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
