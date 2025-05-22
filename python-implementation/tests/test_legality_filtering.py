from engine.moves.generator import legal_moves
from engine.rules import in_check
from tests.utils import (
    make_board,
    print_section,
)


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


def test_in_check():
    print_section("Check Detection")

    # White king in check from black queen
    b = make_board({(5, 1): "K", (5, 8): "q"})
    assert in_check(b, "white"), "White should be in check from e8 queen"

    # Black king not in check
    b = make_board({(5, 8): "k"})
    assert not in_check(b, "black"), "Black king alone should not be in check"

    print("✔️ in_check() correctly detects check state.")
