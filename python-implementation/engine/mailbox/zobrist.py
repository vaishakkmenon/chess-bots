from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.mailbox.board import Board


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
        return PIECE_ORDER.index(piece_char)

    def square_index(self, file: int, rank: int) -> int:
        return (rank - 1) * 8 + (file - 1)

    def compute_hash(self, board: Board, side_to_move: str) -> int:
        hash_key = 0
        for file in range(1, 9):
            for rank in range(1, 9):
                piece = board[file, rank]
                if piece != board.EMPTY:
                    piece_index = self.piece_index(piece)
                    sq_index = self.square_index(file, rank)
                    hash_key ^= self.piece_square[piece_index][sq_index]

        if board.white_can_castle_kingside:
            hash_key ^= self.castling_rights["WK"]
        if board.white_can_castle_queenside:
            hash_key ^= self.castling_rights["WQ"]
        if board.black_can_castle_kingside:
            hash_key ^= self.castling_rights["BK"]
        if board.black_can_castle_queenside:
            hash_key ^= self.castling_rights["BQ"]

        if board.en_passant_target is not None:
            ep_file, ep_rank = board.en_passant_target
            if ep_rank in (3, 6) and 1 <= ep_file <= 8:
                hash_key ^= self.en_passant[ep_file]

        if side_to_move == "black":
            hash_key ^= self.side_to_move

        return hash_key
