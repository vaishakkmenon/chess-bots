from engine.bitboard.moves.rook import generate_rook_moves


# Helper to get sorted (dst, capture) tuples
def dsts_and_caps(moves):
    return sorted((m.dst, m.capture) for m in moves)


def test_rook_open_board_from_d4():
    # Rook on d4 (27), empty board
    src = 27
    rook_bb = 1 << src
    my_occ = 0
    their_occ = 0

    moves = generate_rook_moves(rook_bb, my_occ, their_occ)
    # along file d: d1(3),d2(11),d3(19); d5(35),d6(43),d7(51),d8(59)
    # along rank 4: a4(24),b4(25),c4(26); e4(28),f4(29),g4(30),h4(31)
    expected = sorted(
        [
            (3, False),
            (11, False),
            (19, False),
            (35, False),
            (43, False),
            (51, False),
            (59, False),
            (24, False),
            (25, False),
            (26, False),
            (28, False),
            (29, False),
            (30, False),
            (31, False),
        ]
    )
    assert dsts_and_caps(moves) == expected


def test_rook_blocked_by_friend_and_capture():
    # Rook on d4 (27), friend on d6 (43) blocks north
    # enemy on f4 (29) capturable east
    src = 27
    rook_bb = 1 << src
    my_occ = 1 << 43
    their_occ = 1 << 29

    moves = generate_rook_moves(rook_bb, my_occ, their_occ)
    ds = dsts_and_caps(moves)

    # Should include d5(35) but not d6(43) or beyond
    assert (35, False) in ds
    assert all(dst != 43 for dst, _ in ds)

    # Along east: e4(28) then f4(29, capture) then stop
    assert (28, False) in ds
    assert (29, True) in ds
    assert all(dst not in (30, 31) for dst, _ in ds)


def test_rook_multiple_rooks():
    # Two rooks: a1(0) and h8(63). No blockers.
    rook_bb = (1 << 0) | (1 << 63)
    moves = generate_rook_moves(rook_bb, 0, 0)

    # a1 should generate along rank1: b1(1)...h1(7)
    # and file a: a2(8)...a8(56)
    a1_moves = sorted(m.dst for m in moves if m.src == 0)
    assert a1_moves == [1, 2, 3, 4, 5, 6, 7, 8, 16, 24, 32, 40, 48, 56]

    # h8 should generate along rank8: g8(62)...a8(56)
    # and file h: h7(55)...h1(7)
    h8_moves = sorted(m.dst for m in moves if m.src == 63)
    assert h8_moves == [7, 15, 23, 31, 39, 47, 55, 56, 57, 58, 59, 60, 61, 62]


def test_no_rooks_no_moves():
    assert generate_rook_moves(0, 0, 0) == []


def test_rook_on_a1_blocked_on_rank_and_file():
    # Rook on a1 (0), our own pawns on a2 (8) and b1 (1) block both rays
    rook_bb = 1 << 0
    my_occ = (1 << 8) | (1 << 1)
    their_occ = 0

    moves = generate_rook_moves(rook_bb, my_occ, their_occ)
    # No moves at all, both rank and file are blocked immediately
    assert moves == []


def test_rook_adjacent_capture_and_block():
    # Rook on d4 (27); enemy at d5 (35) and our pawn at d3 (19)
    rook_bb = 1 << 27
    my_occ = 1 << 19  # block south
    their_occ = 1 << 35  # can capture north
    moves = generate_rook_moves(rook_bb, my_occ, their_occ)

    # Should include capture at d5 and nothing beyond
    caps = [(m.dst, m.capture) for m in moves if m.capture]
    assert caps == [(35, True)]
    # Should not include any square south of d3 or beyond d5
    all_dsts = {m.dst for m in moves}
    assert all(d not in all_dsts for d in (11, 3, 43, 51))


def test_rook_midboard_mixed_blockers():
    # Rook on e5 (36)
    rook_bb = 1 << 36
    # Block north at e7 (52), enemy capture south at e4 (28)
    # Block east at g5 (38), enemy capture west at d5 (35)
    my_occ = (1 << 52) | (1 << 38)
    their_occ = (1 << 28) | (1 << 35)
    moves = generate_rook_moves(rook_bb, my_occ, their_occ)
    dc = dsts_and_caps(moves)

    # North: only e6(44) quiet move
    assert (44, False) in dc
    assert all(d != 52 for d, _ in dc)

    # South: only e4(28) capture
    assert (28, True) in dc
    assert all(d not in (19, 11, 3) for d, _ in dc if d < 36)

    # East: only f5(37) quiet move
    assert (37, False) in dc
    assert all(d not in (38, 39) for d, _ in dc if d > 36 and d // 8 == 4)

    # West: only d5(35) capture
    assert (35, True) in dc
    assert all(d not in (34, 33, 32) for d, _ in dc if d < 36 and d // 8 == 4)


def test_rook_single_step_mixed():
    # Rook on b2 (9); enemy on b3(17), friend on c2(10)
    rook_bb = 1 << 9
    my_occ = 1 << 10
    their_occ = 1 << 17
    moves = generate_rook_moves(rook_bb, my_occ, their_occ)
    dc = dsts_and_caps(moves)
    expected = sorted(
        [
            (8, False),  # a2
            (1, False),  # b1
            (17, True),  # b3×
        ]
    )
    assert dc == expected


def test_rook_empty_board_all_edges():
    # Rook on center a5 (32)
    rook_bb = 1 << 32
    moves = generate_rook_moves(rook_bb, 0, 0)
    # Should produce exactly 14 moves: 7 up, 7 right
    assert len(moves) == 14
    # Up: a6(40)..a8(56), Right: b5(33)..h5(39)
    # North: a6(40), a7(48), a8(56)
    # South: a4(24), a3(16), a2(8),  a1(0)
    # East:  b5(33), c5(34), …, h5(39)
    expected = sorted(
        [
            (i, False)
            for i in list(range(40, 64, 8))  # north
            + list(range(24, -1, -8))  # south
            + list(range(33, 40))  # east
        ]
    )
    assert dsts_and_caps(moves) == expected
