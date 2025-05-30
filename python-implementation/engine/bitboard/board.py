from engine.bitboard.move import Move  # noqa: TC002
from engine.bitboard.constants import (
    INITIAL_MASKS,
    WHITE_PAWN,
    BLACK_PAWN,
    WHITE,
    BLACK,
)


class Board:
    def __init__(self):
        # a list of 12 ints, one per piece-type
        self.bitboards = [0] * 12

        # stored occupancy bitboards
        self.white_occ = 0
        self.black_occ = 0
        self.all_occ = 0

        # En_passant flag/square
        self.ep_square = 0

        # Flag to see side to move
        self.side_to_move = WHITE

        self.init_positions()

    def __str__(self):
        """
        Return an ASCII representation with rank/file labels.
        Uppercase: White pieces; lowercase: Black; dot: empty.
        Ranks 8->1, files a->h.
        """
        piece_chars = [
            "P",
            "N",
            "B",
            "R",
            "Q",
            "K",  # White
            "p",
            "n",
            "b",
            "r",
            "q",
            "k",  # Black
        ]
        rows = []
        for rank in range(8, 0, -1):
            row = [str(rank)]
            for file in range(8):
                sq = (rank - 1) * 8 + file
                ch = "."
                for idx, bb in enumerate(self.bitboards):
                    if (bb >> sq) & 1:
                        ch = piece_chars[idx]
                        break
                row.append(ch)
            rows.append(" ".join(row))
        # file labels
        footer = [" "] + [chr(ord("a") + f) for f in range(8)]
        rows.append(" ".join(footer))
        return "\n".join(rows)

    def init_positions(self):
        for idx in range(12):
            self.bitboards[idx] = INITIAL_MASKS[idx]

        # build the occupancy bitboards
        self.update_occupancies()

    def update_occupancies(self):
        """Recompute white_occ, black_occ, and all_occ from self.bitboards."""
        # white pieces are indices 0–5
        w = 0
        for i in range(6):
            w |= self.bitboards[i]
        self.white_occ = w

        # black pieces are indices 6–11
        b = 0
        for i in range(6, 12):
            b |= self.bitboards[i]
        self.black_occ = b

        # full board occupancy
        self.all_occ = self.white_occ | self.black_occ

    def make_move(self, move: Move):
        """
        Execute a move on the board, updating:
         - self.ep_square (en-passant target)
         - self.bitboards (piece positions)
         - self.ep captures
         - self.white_occ / black_occ / all_occ
        """
        old_ep = self.ep_square
        self.ep_square = 0
        src, dst = move.src, move.dst

        piece_idx = None
        for idx in range(12):
            if (self.bitboards[idx] & (1 << src)) != 0:
                piece_idx = idx
                break

        if piece_idx in (WHITE_PAWN, BLACK_PAWN):
            # Check if the move is on the same file as well as a double push
            if (dst % 8) == (src % 8) and abs((dst // 8) - (src // 8)) == 2:
                mid_sq = (src + dst) // 2
                self.ep_square = 1 << mid_sq

        self.bitboards[piece_idx] ^= 1 << src

        if move.capture:
            if piece_idx in (WHITE_PAWN, BLACK_PAWN) and (1 << dst) == old_ep:
                cap_sq = dst - 8 if piece_idx == WHITE_PAWN else dst + 8
            else:
                cap_sq = dst

            for idx in range(12):
                if (self.bitboards[idx] >> cap_sq) & 1:
                    self.bitboards[idx] ^= 1 << cap_sq
                    break

        self.bitboards[piece_idx] |= 1 << dst
        self.update_occupancies()
        self.side_to_move = BLACK if self.side_to_move == WHITE else WHITE
