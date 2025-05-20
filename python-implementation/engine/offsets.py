# File for all pieces offsets/move possibilities

PAWN_ATTACK_OFFSETS = {
    "white": [(-1, -1), (1, -1)],
    "black": [(-1, 1), (1, 1)],
}

KNIGHT_OFFSETS = [
    (2, 1),
    (2, -1),
    (-2, 1),
    (-2, -1),
    (1, 2),
    (1, -2),
    (-1, 2),
    (-1, -2),
]

BISHOP_OFFSETS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_OFFSETS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

QUEEN_OFFSETS = [
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
]

KING_OFFSETS = QUEEN_OFFSETS
