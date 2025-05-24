# tests/test_castling.py
import pytest
from engine.moves.move import Move
from engine.moves.king import king_moves
from tests.utils import make_board


# ─── Helpers ────────────────────────────────────────────────────────────────
def has_castle_move(moves, frm, to):
    return any(
        m.from_sq == frm and m.to_sq == to and m.is_castle for m in moves
    )


# ─── 1. Kingside & Queenside allowed ────────────────────────────────────────
@pytest.mark.parametrize(
    "rook_sq, to_sq", [((8, 1), (7, 1)), ((1, 1), (3, 1))]
)
def test_castling_allowed(rook_sq, to_sq):
    b = make_board({(5, 1): "K", rook_sq: "R"})
    if rook_sq[0] == 8:
        b.white_can_castle_kingside = True
    else:
        b.white_can_castle_queenside = True
    moves = king_moves(b, "white")
    assert has_castle_move(moves, (5, 1), to_sq)


# ─── 2. Path blocked ────────────────────────────────────────────────────────
def test_castling_blocked_path():
    b = make_board({(5, 1): "K", (6, 1): "P", (8, 1): "R"})
    b.white_can_castle_kingside = True
    moves = king_moves(b, "white")
    assert not has_castle_move(moves, (5, 1), (7, 1))


# ─── 3. King in check ───────────────────────────────────────────────────────
def test_castling_king_in_check():
    b = make_board({(5, 1): "K", (8, 1): "R", (5, 8): "q"})
    b.white_can_castle_kingside = True
    assert not has_castle_move(king_moves(b, "white"), (5, 1), (7, 1))


# ─── 4. Square crossed attacked ─────────────────────────────────────────────
def test_castling_crossed_square_attacked():
    b = make_board({(5, 1): "K", (8, 1): "R", (6, 8): "q"})  # queen hits f1
    b.white_can_castle_kingside = True
    assert not has_castle_move(king_moves(b, "white"), (5, 1), (7, 1))


# ─── 5. King not on home square ────────────────────────────────────────────
def test_castling_king_not_home():
    b = make_board({(4, 1): "K", (8, 1): "R"})
    b.white_can_castle_kingside = True
    assert not has_castle_move(king_moves(b, "white"), (4, 1), (6, 1))


# ─── 6. Castling-rights flags update & restore ─────────────────────────────
@pytest.mark.parametrize(
    "start_sq, end_sq, flag",
    [
        (
            (5, 1),
            (5, 2),
            ("white_can_castle_kingside", "white_can_castle_queenside"),
        ),
        ((1, 1), (1, 2), ("white_can_castle_queenside",)),
        ((8, 1), (8, 2), ("white_can_castle_kingside",)),
        ((2, 1), (1, 1), ("white_can_castle_queenside",)),
        ((7, 1), (8, 1), ("white_can_castle_kingside",)),
    ],
)
def test_castling_rights_cleared_and_restored(start_sq, end_sq, flag):
    piece = "K" if start_sq == (5, 1) else "R"
    b = make_board({start_sq: piece})
    for f in flag:
        setattr(b, f, True)

    m = Move(start_sq, end_sq)
    rights = b.make_move(m)
    for f in flag:
        assert not getattr(b, f)
    b.undo_move(m, rights)
    for f in flag:
        assert getattr(b, f)
