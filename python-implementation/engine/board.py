# Board class to build and initialize the board for the game


class Board:

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

    RANKS = 8
    FILES = 8

    def __init__(self):
        self.squares = [
            [self.EMPTY for _ in range(self.FILES)] for _ in range(self.RANKS)
        ]

    def __repr__(self):
        for i in range(self.RANKS):
            for j in range(self.FILES):
                print(f"{self.squares[i][j]} ", end="")
            print()

    def __str__(self) -> str:
        rows = []
        reverse = reversed(self.squares)
        for rank_no, row in zip(range(self.RANKS, 0, -1), reverse):
            rows.append(f"{rank_no} " + " ".join(row))
        rows.append("  a b c d e f g h")
        return "\n".join(rows)


board = Board()
# print(len(board.squares), len(board.squares[0]))  # should be 8, 8
# board.__repr__()
print(board)
