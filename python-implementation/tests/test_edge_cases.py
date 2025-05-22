from engine.moves.move import Move
from engine.moves.generator import legal_moves
from tests.utils import (
    make_board,
    print_section,
)


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
