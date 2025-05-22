from engine.moves.move import Move
from engine.moves.king import king_moves
from tests.utils import (
    make_board,
    assert_true,
    print_section,
)


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
