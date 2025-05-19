# engine/test_full.py

from board import Board
from moves import pawn_moves, knight_moves, all_moves


# Simple assert helpers
def assert_equal(a, b, msg=""):
    if a != b:
        raise AssertionError(f"Assertion failed: {msg} — {a} != {b}")


def assert_true(expr, msg=""):
    if not expr:
        raise AssertionError(f"Assertion failed: {msg}")


def main():
    # 1) Pawn single & double push on empty board
    b = Board()  # empty by default
    b[(2, 2)] = "P"  # white pawn on b2
    p_moves = pawn_moves(b, "white")
    expected = [((2, 2), (2, 3), None), ((2, 2), (2, 4), None)]
    assert_equal(set(p_moves), set(expected), "pawn single+double push")

    # 2) Pawn capture
    b = Board()
    b[(4, 4)] = "P"  # pawn at d4
    b[(5, 5)] = "p"  # enemy on e5
    caps = pawn_moves(b, "white")
    assert_true(((4, 4), (5, 5), None) in caps, "pawn capture at e5")

    # 3) En passant (assumes make_move sets ep target)
    b = Board()
    # place two white pawns
    b[(5, 5)] = "P"  # e5
    # simulate black double-push from d7 to d5
    b[(4, 7)] = "p"
    b.make_move((4, 7), (4, 5), None)
    # now white can ep on d6
    ep_moves = pawn_moves(b, "white")
    assert_true(((5, 5), (4, 6), None) in ep_moves, "en passant from e5 to d6")

    # 4) Promotion (explicit choice)
    b = Board()
    b[(7, 7)] = "P"  # g7
    promos = pawn_moves(b, "white")
    # should include four promotions (to Q, R, B, N) on g8
    pr = [m for m in promos if m[0] == (7, 7) and m[1] == (7, 8)]
    kinds = {m[2] for m in pr}
    assert_equal(kinds, {"Q", "R", "B", "N"}, "promotion choices on g8")

    # 5) Knight on empty board
    b = Board()
    b[(4, 4)] = "N"
    k_moves = knight_moves(b, "white")
    assert_equal(len(k_moves), 8, "knight at d4 has 8 jumps")
    assert_true(((4, 4), (5, 6), None) in k_moves, "d4->e6 present")

    # 6) Knights in starting position
    b = Board()
    b.init_positions()
    wk = knight_moves(b, "white")
    # b1->a3 and b1->c3
    assert_true(((2, 1), (1, 3), None) in wk, "b1->a3")
    assert_true(((2, 1), (3, 3), None) in wk, "b1->c3")

    # 7) all_moves aggregates both
    b = Board()
    b[(2, 2)] = "P"
    b[(4, 4)] = "N"
    allm = all_moves(b, "white")
    # must contain both our pawn and knight moves
    for m in expected + k_moves:
        assert_true(m in allm, f"all_moves missing {m}")

    # 8) Smoke‐test make_move + all_moves interplay
    b = Board()
    b.init_positions()
    # pick a knight from g1->f3
    move = ((7, 1), (6, 3), None)
    b.make_move(move[0], move[1], move[2])
    # now that knight sits on f3
    am = all_moves(b, "white")
    # it should no longer include g1 jumps, but include f3->h4 etc.
    assert_true(((6, 3), (8, 4), None) in am, "f3->h4 after move")
    assert_true(all(m[0] != (7, 1) for m in am), "no moves from g1")

    print("✔️ All full‐suite tests passed!")


if __name__ == "__main__":
    main()
