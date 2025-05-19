# engine/test_pieces.py

from board import Board
from moves.pawn import pawn_moves
from moves.knight import knight_moves
from moves.bishop import bishop_moves

# from moves.helpers import check_bounds


# Simple assertions
def assert_equal(a, b, msg=""):
    if a != b:
        raise AssertionError(f"{msg} — expected {b}, got {a}")


def assert_true(expr, msg=""):
    if not expr:
        raise AssertionError(f"{msg}")


# Helper to build a custom board
def make_board(pieces: dict[tuple[int, int], str]) -> Board:
    """
    Start from an empty board and place only the given pieces.
    `pieces` maps (file,rank) → piece-char, e.g. {(4,4): "B", (2,2): "p"}.
    """
    b = Board()
    for (f, r), char in pieces.items():
        b[(f, r)] = char
    return b


# Utility for clear sections
def print_section(title: str):
    print(f"\n{'='*10} {title} {'='*10}")


def print_board(b: Board):
    print(b)


def test_pawn_moves():
    print_section("Pawn Moves Tests")

    # A) Single & double push
    b = make_board({(2, 2): "P"})
    print("Before Test A: Pawn single & double push")
    print_board(b)
    pm = pawn_moves(b, "white")
    assert_equal(
        set(pm),
        {((2, 2), (2, 3), None), ((2, 2), (2, 4), None)},
        "Pawn single+double push",
    )
    print("Moves:", pm)
    print("After Test A:")
    print_board(b)

    # B) Capture
    b = make_board({(4, 4): "P", (5, 5): "p"})
    print("\nBefore Test B: Pawn capture")
    print_board(b)
    caps = pawn_moves(b, "white")
    assert_true(((4, 4), (5, 5), None) in caps, "Pawn capture e5")
    move = ((4, 4), (5, 5), None)
    b.make_move(move[0], move[1], move[2])
    print("After executing capture d4→e5:")
    print_board(b)

    # C) En passant
    b = make_board({(5, 5): "P", (4, 7): "p"})
    print("\nBefore Test C: En passant setup")
    print_board(b)
    b.make_move((4, 7), (4, 5), None)  # simulate black d7→d5
    print("After black d7->d5:")
    print_board(b)
    ep = pawn_moves(b, "white")
    assert_true(((5, 5), (4, 6), None) in ep, "En passant e5→d6")
    print("En passant moves:", ep)
    # filter just the en passant move (from e5 to d6)
    ep_moves = [m for m in ep if m[1] == (4, 6)]
    assert_equal(len(ep_moves), 1, "Exactly one en passant move available")
    from_sq, to_sq, promo = ep_moves[0]
    b.make_move(from_sq, to_sq, promo)
    print("\nAfter forcing en passant:")
    print_board(b)

    # D) Promotion
    b = make_board({(7, 7): "P"})
    print("\nBefore Test D: Pawn promotion")
    print_board(b)
    pr = pawn_moves(b, "white")
    prom_to = {m[2] for m in pr if m[0] == (7, 7)}
    assert_equal(prom_to, {"Q", "R", "B", "N"}, "Pawn promotion choices")
    print("Promotion options:", pr)


def test_knight_moves():
    print_section("Knight Moves Tests")

    # A) Center jumps (d4)
    b = make_board({(4, 4): "N"})
    print("Before Test A: Knight center jumps")
    print_board(b)
    km = knight_moves(b, "white")
    assert_equal(len(km), 8, "Knight in center has 8 moves")
    print("Moves:", km)

    # B) Blocked by own piece
    b = make_board({(4, 4): "N", (6, 5): "P"})
    print("\nBefore Test B: Knight blocked by own piece")
    print_board(b)
    km2 = knight_moves(b, "white")
    assert_true(((4, 4), (6, 5), None) not in km2, "Own‐piece jump excluded")
    print("Moves:", km2)

    # C) Capture enemy
    b = make_board({(4, 4): "N", (6, 5): "p"})
    print("\nBefore Test C: Knight capture enemy")
    print_board(b)
    km3 = knight_moves(b, "white")
    assert_true(((4, 4), (6, 5), None) in km3, "Enemy‐capture included")
    print("Moves:", km3)


def test_bishop_moves():
    print_section("Bishop Moves Tests")

    # A) Center, empty board
    b = make_board({(4, 4): "B"})
    print("Before Test A: Bishop center on empty board")
    print_board(b)
    bm = bishop_moves(b, "white")
    assert_equal(len(bm), 13, "Bishop center has 13 moves")
    print("Moves:", bm)

    # B) Corner a1
    b = make_board({(1, 1): "B"})
    print("\nBefore Test B: Bishop at a1")
    print_board(b)
    bm2 = bishop_moves(b, "white")
    assert_equal(len(bm2), 7, "Bishop at a1 has 7 moves")
    print("Moves:", bm2)

    # C) Blocked by own pawns NW & NE
    b = make_board({(4, 4): "B", (3, 5): "P", (5, 5): "P"})
    print("\nBefore Test C: Bishop blocked NW/NE")
    print_board(b)
    bm3 = bishop_moves(b, "white")
    assert_equal(len(bm3), 6, "Blocked bishop = 6 moves")
    print("Moves:", bm3)

    # D) Single enemy capture then stop
    b = make_board({(4, 4): "B", (2, 2): "p"})
    print("\nBefore Test D: Bishop capture then stop")
    print_board(b)
    bm4 = bishop_moves(b, "white")
    assert_true(((4, 4), (2, 2), None) in bm4, "d4→b2 capture")
    assert_true(all(m[1] != (1, 1) for m in bm4), "No moves past b2")
    print("Moves:", bm4)


if __name__ == "__main__":
    test_pawn_moves()
    test_knight_moves()
    test_bishop_moves()
    print("\n✔️ All piece‐specific tests passed!")
