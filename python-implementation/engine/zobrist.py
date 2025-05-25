import random

PIECE_ORDER = [
    "P",
    "N",
    "B",
    "R",
    "Q",
    "K",
    "p",
    "n",
    "b",
    "r",
    "q",
    "k",
]

NUM_SQUARES = 64

# Castling rights identifiers in order: WK, WQ, BK, BQ
CASTLING_RIGHTS = ["WK", "WQ", "BK", "BQ"]

# En passant files: 1 through 8 (a to h)
EN_PASSANT_FILES = list(range(1, 9))


class Zobrist:
    def __init__(self):
        self.rng = random.Random(69)
        self.piece_square = [
            [self.rng.getrandbits(64) for _ in range(64)] for _ in PIECE_ORDER
        ]
        self.castling_rights = {
            cr: self.rng.getrandbits(64) for cr in CASTLING_RIGHTS
        }
        self.en_passant = {
            file: self.rng.getrandbits(64) for file in EN_PASSANT_FILES
        }
        self.side_to_move = self.rng.getrandbits(64)

    def piece_index(self, piece_char: str) -> int:
        """Get index of piece in PIECE_ORDER"""
        return PIECE_ORDER.index(piece_char)

    def square_index(self, file: int, rank: int) -> int:
        """Map (file, rank) to 0-based square index"""
        return (rank - 1) * 8 + (file - 1)
