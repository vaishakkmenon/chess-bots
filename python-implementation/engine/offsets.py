# File for all pieces offsets/move possibilities

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

QUEEN_OFFSETS = BISHOP_OFFSETS + ROOK_OFFSETS
