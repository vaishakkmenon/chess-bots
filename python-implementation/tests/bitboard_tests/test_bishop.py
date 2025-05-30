from engine.bitboard.move import Move
from engine.bitboard.moves.bishop import generate_bishop_moves


# Helper to extract destinations and capture flags
def dsts_and_caps(moves):
    return sorted([(m.dst, m.capture) for m in moves])


def test_bishop_open_board_from_d4():
    # Bishop on d4 (sq=27), empty board
    src = 27
    bishops_bb = 1 << src
    my_occ = 0
    their_occ = 0

    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    # Expected destinations (13 squares) all non-captures
    expected_dsts = sorted(
        [
            # NW: c5, b6, a7
            34,
            41,
            48,
            # NE: e5, f6, g7, h8
            36,
            45,
            54,
            63,
            # SW: c3, b2, a1
            18,
            9,
            0,
            # SE: e3, f2, g1
            20,
            13,
            6,
        ]
    )
    got = sorted(m.dst for m in moves)
    assert got == expected_dsts
    assert all(not m.capture for m in moves)


def test_bishop_blocked_by_friend_on_b6():
    # Bishop on d4, our pawn on b6 blocks NW ray
    src = 27
    bishops_bb = 1 << src
    my_occ = 1 << 41  # b6
    their_occ = 0

    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    # NW ray should only include c5 (34), then stop
    assert (34, False) in dsts_and_caps(moves)
    assert all(dst not in (41, 48) for dst, cap in dsts_and_caps(moves))


def test_bishop_capture_enemy_on_f6():
    # Bishop on d4, enemy pawn on f6
    src = 27
    bishops_bb = 1 << src
    my_occ = 0
    their_occ = 1 << 45  # f6

    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    # Along NE: should have quiet e5 (36) then capture f6 (45) and stop
    seq = [m for m in moves if m.src == src]
    # Extract NE moves sorted by dst
    ne_moves = [m for m in seq if m.dst in (36, 45)]
    assert dsts_and_caps(ne_moves) == [(36, False), (45, True)]
    # Should not include g7(54) or h8(63)
    assert all(dst not in (54, 63) for dst, _ in dsts_and_caps(seq))


def test_bishop_multiple_pieces():
    # Two bishops: one at c1 (2), one at f4 (29). Mix of captures.
    bishops_bb = (1 << 2) | (1 << 29)
    # place our pawn at d2(11) to block c1→d2
    # place enemy pawn at h8(63) to be captured by f4→g5→h6→...
    # but bishop can't reach h8 diagonally from f4
    my_occ = 1 << 11
    their_occ = 1 << 36  # e5
    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)
    # c1 (2) should not generate move to d2 (blocked) or beyond
    assert all(not (m.src == 2 and m.dst == 11) for m in moves)
    # f4 (29) should generate capture at e5 (36)
    assert Move(29, 36, capture=True) in moves


def test_no_bishops_no_moves():
    # Empty bishop bitboard → no moves
    assert generate_bishop_moves(0, 0, 0) == []


def test_bishop_from_a1_full_ne_traverse():
    # Bishop on a1 (sq=0) should sweep NE to b2(9), c3(18), ..., h8(63)
    src = 0
    bishops_bb = 1 << src
    moves = generate_bishop_moves(bishops_bb, my_occ=0, their_occ=0)
    expected_dsts = [9, 18, 27, 36, 45, 54, 63]
    got = sorted(m.dst for m in moves)
    assert got == expected_dsts
    assert all(not m.capture for m in moves)


def test_bishop_from_h8_full_sw_traverse():
    # Bishop on h8 (sq=63) should sweep SW to g7(54), f6(45), ..., a1(0)
    src = 63
    bishops_bb = 1 << src
    moves = generate_bishop_moves(bishops_bb, my_occ=0, their_occ=0)
    expected_dsts = [54, 45, 36, 27, 18, 9, 0]
    got = sorted(
        (m.dst for m in moves), reverse=True
    )  # or sort ascending and compare sorted lists
    assert sorted(got) == sorted(expected_dsts)
    assert all(not m.capture for m in moves)


def test_bishop_adjacent_capture_and_block():
    # Bishop on c1 (sq=2), enemy on b2 (sq=9) and our own on a3 (sq=16)
    bishops_bb = 1 << 2
    my_occ = 1 << 16  # block SW beyond
    their_occ = 1 << 9  # capture SW
    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)

    # Should include capture at b2, then stop—no move to a3
    cap_moves = [(m.dst, m.capture) for m in moves if m.capture]
    assert cap_moves == [(9, True)]
    assert all(m.dst != 16 for m in moves)


def test_bishop_fully_blocked_by_friends():
    # Bishop on d4 (27), our pawns on all 4 diagonals at distance 1
    bishops_bb = 1 << 27
    my_occ = sum(1 << sq for sq in [18, 20, 34, 36])  # c3, e3, c5, e5
    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ=0)

    # None of those four adjacent squares or beyond should appear
    assert all(m.dst not in (18, 20, 34, 36) for m in moves)
    # And since every ray is blocked at distance 1, there should be 0 moves
    assert moves == []


def test_bishop_long_ray_with_mixed_blockers():
    # Bishop on e3 (sq=20)
    bishops_bb = 1 << 20
    # friendly at g5 (38) blocks NE after one step; enemy at c1 (2) on SW
    my_occ = 1 << 38
    their_occ = 1 << 2
    moves = generate_bishop_moves(bishops_bb, my_occ, their_occ)

    # NE ray: should produce f4 (29) then stop before g5
    ne = [m for m in moves if m.src == 20 and m.dst in (29, 38)]
    assert [(m.dst, m.capture) for m in ne] == [(29, False)]

    # SW ray: should produce d2 (11), c1 (2 capture), then stop
    sw = [m for m in moves if m.src == 20 and m.dst in (11, 2)]
    assert [(m.dst, m.capture) for m in sw] == [(11, False), (2, True)]
