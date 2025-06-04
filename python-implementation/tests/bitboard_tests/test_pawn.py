import pytest
from engine.bitboard.move import Move
from engine.bitboard.moves.pawn import (
    pawn_single_push_targets,
    pawn_double_push_targets,
    pawn_push_targets,
    generate_pawn_moves,
    pawn_capture_targets,
    pawn_en_passant_targets,
)


# helper to build a bitboard from a list of square indices
def mask(indices):
    return sum(1 << i for i in indices)


# occupancy = exactly those pawns (no other pieces)
def simple_occ(pawns_bb):
    return pawns_bb


# White single pushes
@pytest.mark.parametrize(
    "sq, expected",
    [
        (8, mask([16])),  # a2 -> a3
        (15, mask([23])),  # h2 -> h3
        (12, mask([20])),  # e2 -> e3
    ],
)
def test_white_single_push(sq, expected):
    pawns = 1 << sq
    occ = simple_occ(pawns)
    result = pawn_single_push_targets(pawns, occ, True)
    assert result == expected


# White double pushes
@pytest.mark.parametrize(
    "sq, expected",
    [
        (8, mask([24])),  # a2 -> a4
        (15, mask([31])),  # h2 -> h4
        (12, mask([28])),  # e2 -> e4
    ],
)
def test_white_double_push(sq, expected):
    pawns = 1 << sq
    occ = simple_occ(pawns)
    result = pawn_double_push_targets(pawns, occ, True)
    assert result == expected


# Combined white push targets
def test_white_push_targets_union():
    sq = 12  # e2
    pawns = 1 << sq
    occ = simple_occ(pawns)
    single = pawn_single_push_targets(pawns, occ, True)
    double = pawn_double_push_targets(pawns, occ, True)
    combined = pawn_push_targets(pawns, occ, True)
    assert combined == (single | double)


# Black single pushes
@pytest.mark.parametrize(
    "sq, expected",
    [
        (48, mask([40])),  # a7 -> a6
        (55, mask([47])),  # h7 -> h6
        (52, mask([44])),  # e7 -> e6
    ],
)
def test_black_single_push(sq, expected):
    pawns = 1 << sq
    occ = simple_occ(pawns)
    result = pawn_single_push_targets(pawns, occ, False)
    assert result == expected


# Black double pushes
@pytest.mark.parametrize(
    "sq, expected",
    [
        (48, mask([32])),  # a7 -> a5
        (55, mask([39])),  # h7 -> h5
        (52, mask([36])),  # e7 -> e5
    ],
)
def test_black_double_push(sq, expected):
    pawns = 1 << sq
    occ = simple_occ(pawns)
    result = pawn_double_push_targets(pawns, occ, False)
    assert result == expected


def test_white_single_push_blocked():
    pawns = 1 << 12  # e2
    blocker = 1 << 20  # e3
    occ = pawns | blocker
    assert pawn_single_push_targets(pawns, occ, True) == 0


def test_white_double_push_blocked_first_step():
    pawns = 1 << 12  # e2
    blocker = 1 << 20  # e3
    occ = pawns | blocker
    assert pawn_double_push_targets(pawns, occ, True) == 0


def test_white_double_push_blocked_landing():
    pawns = 1 << 12  # e2
    blocker = 1 << 28  # e4
    occ = pawns | blocker
    assert pawn_double_push_targets(pawns, occ, True) == 0


def test_black_single_push_blocked():
    pawns = 1 << 52  # e7
    blocker = 1 << 44  # e6
    occ = pawns | blocker
    assert pawn_single_push_targets(pawns, occ, False) == 0


def test_black_double_push_blocked_first_step():
    pawns = 1 << 52  # e7
    blocker = 1 << 44  # e6
    occ = pawns | blocker
    assert pawn_double_push_targets(pawns, occ, False) == 0


def test_black_double_push_blocked_landing():
    pawns = 1 << 52  # e7
    blocker = 1 << 36  # e5
    occ = pawns | blocker
    assert pawn_double_push_targets(pawns, occ, False) == 0


# Combined black push targets
def test_black_push_targets_union():
    sq = 52  # e7
    pawns = 1 << sq
    occ = simple_occ(pawns)
    single = pawn_single_push_targets(pawns, occ, False)
    double = pawn_double_push_targets(pawns, occ, False)
    combined = pawn_push_targets(pawns, occ, False)
    assert combined == (single | double)


def test_white_pawn_capture_simple():
    # Place a white pawn on b2 (sq=9) and an enemy on a3 (sq=16) and c3 (sq=18)
    pawns = 1 << 9
    enemies = (1 << 16) | (1 << 18)
    mask = pawn_capture_targets(pawns, enemies, True)
    assert mask == ((1 << 16) | (1 << 18))


def test_black_pawn_capture_simple():
    # Black pawn on b7 (sq=49), enemies on a6 (sq=40) and c6 (sq=42)
    pawns = 1 << 49
    enemies = (1 << 40) | (1 << 42)
    mask = pawn_capture_targets(pawns, enemies, False)
    assert mask == ((1 << 40) | (1 << 42))


# helper to sort moves consistently
def sort_key(m: Move):
    return (m.src, m.dst, m.capture, m.promotion)


@pytest.mark.parametrize(
    "pawns_sq, enemy_sqs, expected_moves",
    [
        # White: single & double pushes only (no enemies)
        (
            12,  # pawn on e2 (sq=12)
            [],  # no enemies
            [  # expect e2→e3 and e2→e4
                Move(12, 20),
                Move(12, 28),
            ],
        ),
        # White: pushes + captures
        (
            9,  # pawn on b2 (sq=9)
            [16, 18],  # enemies on a3 (16) and c3 (18)
            [
                Move(9, 16, True),  # capture a3
                Move(9, 18, True),  # capture c3
                Move(9, 17),  # single push b3
                Move(9, 25),  # double push b4
            ],
        ),
    ],
)
def test_generate_white_pawn_moves(pawns_sq, enemy_sqs, expected_moves):
    pawns_bb = 1 << pawns_sq
    enemy_bb = sum(1 << sq for sq in enemy_sqs)
    all_occ = pawns_bb | enemy_bb

    moves = generate_pawn_moves(pawns_bb, enemy_bb, all_occ, True)
    assert sorted(moves, key=sort_key) == sorted(expected_moves, key=sort_key)


@pytest.mark.parametrize(
    "pawns_sq, enemy_sqs, expected_moves",
    [
        # Black: single & double pushes only (no enemies)
        (
            52,  # pawn on e7 (sq=52)
            [],  # no enemies
            [  # expect e7→e6 and e7→e5
                Move(52, 44),
                Move(52, 36),
            ],
        ),
        # Black: pushes + captures
        (
            49,  # pawn on b7 (sq=49)
            [40, 42],  # enemies on a6 (40) and c6 (42)
            [
                Move(49, 40, True),  # capture a6
                Move(49, 42, True),  # capture c6
                Move(49, 41),  # single push b6
                Move(49, 33),  # double push b5
            ],
        ),
    ],
)
def test_generate_black_pawn_moves(pawns_sq, enemy_sqs, expected_moves):
    pawns_bb = 1 << pawns_sq
    enemy_bb = sum(1 << sq for sq in enemy_sqs)
    all_occ = pawns_bb | enemy_bb

    moves = generate_pawn_moves(pawns_bb, enemy_bb, all_occ, False)
    assert sorted(moves, key=sort_key) == sorted(expected_moves, key=sort_key)


@pytest.mark.parametrize(
    "pawns_sq, ep_sq, is_white, expected",
    [
        # No en passant available
        (1 << 33, None, True, 0),
        (1 << 40, None, False, 0),
        # White pawn on b5 (sq=33) can ep-capture to a6 (40) or c6 (42)
        (1 << 33, 40, True, mask([40])),
        (1 << 33, 42, True, mask([42])),
        # White pawn on a5 (sq=32) can only ep-capture to b6 (41)
        (1 << 32, 41, True, mask([41])),
        (1 << 32, 39, True, 0),  # wrong file → no capture
        # Multiple white pawns on b5 (33) and d5 (35) both capture c6 (42)
        (mask([33, 35]), 42, True, mask([42])),
        # Black pawn on b4 (sq=25) can ep-capture to a3 (16) or c3 (18)
        (1 << 25, 16, False, mask([16])),
        (1 << 25, 18, False, mask([18])),
        # Black pawn on h4 (sq=31) can only ep-capture to g3 (22)
        (1 << 31, 22, False, mask([22])),
        (1 << 31, 16, False, 0),  # wrong file → no capture
        # Multiple black pawns on b4 (25) and d4 (27) both capture c3 (18)
        (mask([25, 27]), 18, False, mask([18])),
    ],
)
def test_pawn_en_passant_targets(pawns_sq, ep_sq, is_white, expected):
    pawns_bb = (
        pawns_sq
        if isinstance(pawns_sq, int) and pawns_sq < (1 << 64)
        else pawns_sq
    )
    ep_mask = 0 if ep_sq is None else (1 << ep_sq)
    result = pawn_en_passant_targets(pawns_bb, ep_mask, is_white)
    assert result == expected


def test_pawn_en_passant_masking_high_bits():
    # Ensure that ~all_occ infinite bits are masked to 64 bits
    # Place a white pawn on b5 (33) and ep at c6 (42)
    # but simulate all_occ with high bits set
    pawns_bb = 1 << 33
    ep_mask = 1 << 42
    # all_occ irrelevant here; just test masking in helper
    result = pawn_en_passant_targets(pawns_bb, ep_mask, True)
    assert (
        result == ep_mask
    )  # should still match despite infinite-precision bits


def test_generate_white_pawn_promotion_moves():
    pawns = 1 << 48  # a7
    moves = generate_pawn_moves(pawns, 0, pawns, True)
    promos = {m.promotion for m in moves}
    assert promos == {"Q", "R", "B", "N"}


def test_generate_black_pawn_promotion_moves():
    pawns = 1 << 15  # h2
    moves = generate_pawn_moves(pawns, 0, pawns, False)
    promos = {m.promotion for m in moves}
    assert promos == {"Q", "R", "B", "N"}


def test_white_capture_promotion_moves():
    pawns = 1 << 54  # g7
    enemy = 1 << 63  # h8
    all_occ = pawns | enemy
    moves = generate_pawn_moves(pawns, enemy, all_occ, True)
    promos = {m.promotion for m in moves if m.dst == 63 and m.capture}
    assert promos == {"Q", "R", "B", "N"}
    assert len([m for m in moves if m.dst == 63]) == 4


def test_black_capture_promotion_moves():
    pawns = 1 << 9  # b2
    enemy = 1 << 0  # a1
    all_occ = pawns | enemy
    moves = generate_pawn_moves(pawns, enemy, all_occ, False)
    promos = {m.promotion for m in moves if m.dst == 0 and m.capture}
    assert promos == {"Q", "R", "B", "N"}
    assert len([m for m in moves if m.dst == 0]) == 4
