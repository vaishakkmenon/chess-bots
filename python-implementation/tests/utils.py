def assert_equal(a, b, msg=""):
    if a != b:
        raise AssertionError(f"{msg} — expected {b}, got {a}")


def assert_true(expr, msg=""):
    if not expr:
        raise AssertionError(f"{msg}")


def make_board(pieces: dict[tuple[int, int], str]):
    from engine.mailbox.board import Board
    from engine.mailbox.zobrist import Zobrist

    b = Board(Zobrist())
    for r in range(1, 9):
        for f in range(1, 9):
            b[(f, r)] = b.EMPTY

    for (f, r), char in pieces.items():
        b[(f, r)] = char

    b.zobrist_hash = b.zobrist.compute_hash(b, "white")
    return b


def print_section(title: str):
    print(f"\n{'='*10} {title} {'='*10}")


def is_single_push(move, color):
    f0, r0 = move.from_sq
    f1, r1 = move.to_sq
    direction = 1 if color == "white" else -1
    return move.promo is None and f0 == f1 and r1 - r0 == direction


def is_double_push(move, color):
    f0, r0 = move.from_sq
    f1, r1 = move.to_sq
    direction = 1 if color == "white" else -1
    return move.promo is None and f0 == f1 and r1 - r0 == 2 * direction


def is_capture(move, color):
    f0, r0 = move.from_sq
    f1, r1 = move.to_sq
    direction = 1 if color == "white" else -1
    return move.promo is None and abs(f1 - f0) == 1 and r1 - r0 == direction


def is_en_passant(move, ep_target):
    return move.is_en_passant and move.to_sq == ep_target


def is_promotion(move):
    return move.promo in {"Q", "R", "B", "N"}
