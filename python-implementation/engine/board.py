# Board class to build and initialize the board for the game


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

    def __init__(self):
        self.squares = [
            [self.EMPTY for _ in range(self.FILES)] for _ in range(self.RANKS)
        ]
        # Used to record if a pawn made a double move for possible en passant
        self.en_passant_target = None

    def __str__(self) -> str:
        rows = []
        reverse = reversed(self.squares)
        for rank_no, row in zip(range(self.RANKS, 0, -1), reverse):
            rows.append(f"{rank_no}| " + " ".join(row))
        rows.append(" |----------------")
        rows.append("   a b c d e f g h")
        return "\n".join(rows)

    def __getitem__(self, pos: tuple[int, int]) -> str:
        file, rank = pos
        return self.squares[rank - 1][file - 1]

    def __setitem__(self, pos: tuple[int, int], piece: str):
        file, rank = pos
        self.squares[rank - 1][file - 1] = piece

    def init_positions(self):
        for i in range(self.RANKS):
            for j in range(self.FILES):
                self.squares[i][j] = self.EMPTY

        for f in range(self.FILES):
            self.squares[1][f] = self.PIECES["WP"]
            self.squares[6][f] = self.PIECES["BP"]

        WHITEPIECES = ["WR", "WN", "WB", "WQ", "WK", "WB", "WN", "WR"]
        BLACKPIECES = ["BR", "BN", "BB", "BQ", "BK", "BB", "BN", "BR"]
        for f in range(self.FILES):
            self.squares[0][f] = self.PIECES[WHITEPIECES[f]]
            self.squares[7][f] = self.PIECES[BLACKPIECES[f]]

    def make_move(
        self,
        from_sq: tuple[int, int],
        to_sq: tuple[int, int],
        promo: str | None = None,
    ) -> None:

        from_f, from_r = from_sq
        to_f, to_r = to_sq

        # Remove piece that is being captured
        ep = self.en_passant_target
        if ep is not None and to_sq == ep:
            pawn = self[from_sq]
            direction = 1 if pawn.isupper() else -1
            remove_rank = to_r - direction
            self[(to_f, remove_rank)] = self.EMPTY

        # Move piece that is capturing
        piece = self[from_sq]
        if promo:
            assert piece.upper() == "P", "Promotion piece is not a pawn!"
            self[to_sq] = promo
        else:
            self[to_sq] = piece
        self[from_sq] = self.EMPTY

        # Check if piece being moved is a pawn and update state
        if piece.upper() == "P" and abs(to_r - from_r) == 2:
            self.en_passant_target = (
                from_f,
                (to_r + from_r) // 2,
            )
        else:
            self.en_passant_target = None
