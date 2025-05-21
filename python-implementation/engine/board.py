# board.py

from typing import Optional, Tuple


class Board:
    RANKS = 8
    FILES = 8

    WHITE_PROMOTE_RANK = 8
    BLACK_PROMOTE_RANK = 1

    EMPTY = "."
    PIECES = {
        "WP": "P",
        "WN": "N",
        "WB": "B",
        "WR": "R",
        "WQ": "Q",
        "WK": "K",
        "BP": "p",
        "BN": "n",
        "BB": "b",
        "BR": "r",
        "BQ": "q",
        "BK": "k",
    }

    @property
    def white_pieces(self) -> frozenset:
        return frozenset(
            self.PIECES[c] for c in self.PIECES if c.startswith("W")
        )

    @property
    def black_pieces(self) -> frozenset:
        return frozenset(
            self.PIECES[c] for c in self.PIECES if c.startswith("B")
        )

    def __init__(self):
        # 0-based internal grid
        self.squares = [
            [self.EMPTY for _ in range(self.FILES)] for _ in range(self.RANKS)
        ]
        # en passant target square
        self.en_passant_target: Optional[Tuple[int, int]] = None
        # castling rights flags
        self.white_can_castle_kingside = True
        self.white_can_castle_queenside = True
        self.black_can_castle_kingside = True
        self.black_can_castle_queenside = True

    def __str__(self) -> str:
        rows = []
        for rank_no in range(self.RANKS, 0, -1):
            row = self.squares[rank_no - 1]
            rows.append(f"{rank_no}| " + " ".join(row))
        rows.append(" |" + "-" * (self.FILES * 2 - 1))
        rows.append("   " + " ".join("abcdefgh"[: self.FILES]))
        return "\n".join(rows)

    def _to_idx(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        file, rank = pos
        return rank - 1, file - 1

    def __getitem__(self, pos: Tuple[int, int]) -> str:
        r, c = self._to_idx(pos)
        return self.squares[r][c]

    def __setitem__(self, pos: Tuple[int, int], piece: str):
        r, c = self._to_idx(pos)
        self.squares[r][c] = piece

    def is_empty(self, pos: Tuple[int, int]) -> bool:
        return self[pos] == self.EMPTY

    def is_white(self, pos: Tuple[int, int]) -> bool:
        p = self[pos]
        return p != self.EMPTY and p.isupper()

    def is_black(self, pos: Tuple[int, int]) -> bool:
        p = self[pos]
        return p != self.EMPTY and p.islower()

    def holds(
        self, pos: Tuple[int, int], chars: Tuple[str, ...] | frozenset
    ) -> bool:
        return self[pos] in chars

    def init_positions(self) -> None:
        """
        Set up the standard starting position.
        """
        # clear board
        for r in range(self.RANKS):
            for c in range(self.FILES):
                self.squares[r][c] = self.EMPTY

        # pawns
        for file in range(1, self.FILES + 1):
            self[(file, 2)] = self.PIECES["WP"]
            self[(file, 7)] = self.PIECES["BP"]

        # back ranks via conventional ordering
        order = "RNBQKBNR"
        for file, piece_code in enumerate(order, start=1):
            self[(file, 1)] = self.PIECES[f"W{piece_code}"]
            self[(file, 8)] = self.PIECES[f"B{piece_code}"]

    def make_move(
        self,
        from_sq: Tuple[int, int],
        to_sq: Tuple[int, int],
        promo: Optional[str] = None,
    ) -> None:
        # handle en passant capture
        ep = self.en_passant_target
        if ep and to_sq == ep:
            pawn = self[from_sq]
            direction = 1 if pawn.isupper() else -1
            self[(to_sq[0], to_sq[1] - direction)] = self.EMPTY

        # move or promotion
        piece = self[from_sq]
        # Track which piece was captured
        captured = self[to_sq]

        # If the piece captured was a rook, then castling is disabled
        if captured == "R" and to_sq == (1, 1):
            self.white_can_castle_queenside = False
        elif captured == "R" and to_sq == (8, 1):
            self.white_can_castle_kingside = False
        elif captured == "r" and to_sq == (1, 8):
            self.black_can_castle_queenside = False
        elif captured == "r" and to_sq == (8, 8):
            self.black_can_castle_kingside = False

        # If the king is castling then move the rook
        if piece.upper() == "K" and abs(to_sq[0] - from_sq[0]) == 2:
            rank = from_sq[1]
            if to_sq[0] > from_sq[0]:
                self[(6, rank)] = self[(8, rank)]
                self[(8, rank)] = self.EMPTY
            else:
                self[(4, rank)] = self[(1, rank)]
                self[(1, rank)] = self.EMPTY

        # Disable castling after the king moves
        if piece == "K":
            self.white_can_castle_kingside = False
            self.white_can_castle_queenside = False
        elif piece == "k":
            self.black_can_castle_kingside = False
            self.black_can_castle_queenside = False
        elif piece == "R" and from_sq == (1, 1):
            self.white_can_castle_queenside = False
        elif piece == "R" and from_sq == (8, 1):
            self.white_can_castle_kingside = False
        elif piece == "r" and from_sq == (1, 8):
            self.black_can_castle_queenside = False
        elif piece == "r" and from_sq == (8, 8):
            self.black_can_castle_kingside = False

        # Allow Promotions
        if promo:
            assert piece.upper() == "P", "Promotion only for pawns"
            self[to_sq] = promo
        else:
            self[to_sq] = piece
        self[from_sq] = self.EMPTY

        # update en passant state
        if piece.upper() == "P" and abs(to_sq[1] - from_sq[1]) == 2:
            self.en_passant_target = (
                from_sq[0],
                (from_sq[1] + to_sq[1]) // 2,
            )
        else:
            self.en_passant_target = None
