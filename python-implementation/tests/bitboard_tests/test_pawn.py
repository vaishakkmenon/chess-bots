import pytest
from engine.bitboard.move import Move
from engine.bitboard.moves.pawn import (
    pawn_single_push_targets,
    pawn_double_push_targets,
    pawn_push_targets,
    generate_pawn_moves,
    pawn_capture_targets,
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
