from engine.moves.generator import legal_moves
from engine.rules import in_check
from tests.utils import (
    make_board,
    print_section,
)


def test_king_escape_squares_exact():
    b = make_board({(5, 1): "K", (5, 8): "r"})
    legal = legal_moves(b, "white")
    assert {m.to_sq for m in legal} == {(4, 1), (4, 2), (6, 1), (6, 2)}


def test_king_can_move_to_d1():
    b = make_board({(5, 1): "K", (5, 8): "r"})
    b[(4, 1)] = "."  # clear d1
    legal = legal_moves(b, "white")
    assert (4, 1) in {m.to_sq for m in legal}


def test_in_check():
    print_section("Check Detection")

    # White king in check from black queen
    b = make_board({(5, 1): "K", (5, 8): "q"})
    assert in_check(b, "white"), "White should be in check from e8 queen"

    # Black king not in check
    b = make_board({(5, 8): "k"})
    assert not in_check(b, "black"), "Black king alone should not be in check"

    print("✔️ in_check() correctly detects check state.")


# En‑passant that leaves king in check must be filtered
def test_ep_illegal_due_to_discovered_check():
    b = make_board({(5, 5): "P", (6, 5): "p", (5, 1): "K", (5, 8): "r"})
    b.en_passant = (6, 6)
    legal = legal_moves(b, "white")
    assert not any(getattr(m, "is_en_passant", False) for m in legal)


# Pinned rook may move along pin line but not off it
def test_rook_along_pin_only():
    b = make_board({(5, 1): "K", (1, 1): "r", (4, 1): "R"})
    legal = legal_moves(b, "white")
    moves = [m for m in legal if m.from_sq == (4, 1)]
    assert all(m.to_sq[1] == 1 for m in moves)  # must stay on rank1


def test_blocking_check_is_legal():
    # Queen a5 gives diagonal check: a5-b4-c3-d2-e1
    b = make_board({(5, 1): "K", (1, 5): "q", (3, 3): "B"})  # bishop c3
    blocking_moves = [
        m for m in legal_moves(b, "white") if m.from_sq == (3, 3)
    ]
    assert (4, 2) in {
        m.to_sq for m in blocking_moves
    }, "Move that blocks the check must be legal"


def test_capturing_checking_piece_is_legal():
    # Same geometry as LF-1; bishop can also capture the queen
    b = make_board({(5, 1): "K", (1, 5): "q", (3, 3): "B"})
    capture_moves = [m for m in legal_moves(b, "white") if m.from_sq == (3, 3)]
    assert (1, 5) in {
        m.to_sq for m in capture_moves
    }, "Capturing the checking piece should be a legal reply to check"
