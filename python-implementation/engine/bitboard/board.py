from typing import List

from engine.bitboard.move import Move  # noqa: TC002
from engine.bitboard.undo import Undo
from .attack_utils import is_square_attacked as _is_square_attacked
from engine.bitboard.constants import (
    INITIAL_MASKS,
    WHITE_PAWN,
    BLACK_PAWN,
    WHITE_KNIGHT,
    BLACK_KNIGHT,
    WHITE_BISHOP,
    BLACK_BISHOP,
    WHITE_ROOK,
    BLACK_ROOK,
    WHITE_QUEEN,
    BLACK_QUEEN,
    WHITE_KING,
    BLACK_KING,
    WHITE,
    BLACK,
)

PROMO_MAP_WHITE = {
    "N": WHITE_KNIGHT,
    "B": WHITE_BISHOP,
    "R": WHITE_ROOK,
    "Q": WHITE_QUEEN,
}
PROMO_MAP_BLACK = {
    "N": BLACK_KNIGHT,
    "B": BLACK_BISHOP,
    "R": BLACK_ROOK,
    "Q": BLACK_QUEEN,
}


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

        # History of all moves
        self.history: List[Undo] = []

        # Flag to see side to move
        self.side_to_move = WHITE

        # Castling rights
        self.castling_rights: int = 0

        # Initialize starting positions
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
        # Add in that all castling should be allowed
        # No king or rook moves have been made
        self.castling_rights = 0b1111  # 1|2|4|8 = 15

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

    def is_square_attacked(self, square: int, attacker_side: int) -> bool:
        """Return ``True`` if ``square`` is attacked by ``attacker_side``."""
        return _is_square_attacked(self, square, attacker_side)

    def in_check(self, side: int) -> bool:
        """Return True if `side`'s king is attacked on this board."""
        if side == WHITE:
            king_bb = self.bitboards[WHITE_KING]
        else:
            king_bb = self.bitboards[BLACK_KING]

        if king_bb == 0:
            return False

        king_sq = king_bb.bit_length() - 1
        attacker = BLACK if side == WHITE else WHITE
        return _is_square_attacked(self, king_sq, attacker)

    def make_move(self, move: Move):
        """
        Execute a move on the board, updating:
         - self.ep_square (en-passant target)
         - self.bitboards (piece positions)
         - self.ep captures
         - self.white_occ / black_occ / all_occ
        """
        old_ep = self.ep_square
        prev_side = self.side_to_move
        self.ep_square = 0
        captured_idx = None
        cap_sq = None
        old_castling_rights = self.castling_rights
        src, dst = move.src, move.dst

        piece_idx = None
        for idx in range(12):
            if (self.bitboards[idx] & (1 << src)) != 0:
                piece_idx = idx
                break

        # Update castling rights if king or rook moves out of original position
        if piece_idx == WHITE_KING:
            self.castling_rights &= ~0b0011
        elif piece_idx == BLACK_KING:
            self.castling_rights &= ~0b1100
        elif piece_idx == WHITE_ROOK:
            if src == 0:
                self.castling_rights &= ~0b0010
            elif src == 7:
                self.castling_rights &= ~0b0001
        elif piece_idx == BLACK_ROOK:
            if src == 56:
                self.castling_rights &= ~0b1000
            elif src == 63:
                self.castling_rights &= ~0b0100

        # If this is a castling move, also move the rook
        if move.castling:
            if piece_idx == WHITE_KING and src == 4 and dst == 6:
                self.bitboards[WHITE_ROOK] ^= 1 << 7
                self.bitboards[WHITE_ROOK] |= 1 << 5
            elif piece_idx == WHITE_KING and src == 4 and dst == 2:
                self.bitboards[WHITE_ROOK] ^= 1 << 0
                self.bitboards[WHITE_ROOK] |= 1 << 3
            elif piece_idx == BLACK_KING and src == 60 and dst == 62:
                self.bitboards[BLACK_ROOK] ^= 1 << 63
                self.bitboards[BLACK_ROOK] |= 1 << 61
            elif piece_idx == BLACK_KING and src == 60 and dst == 58:
                self.bitboards[BLACK_ROOK] ^= 1 << 56
                self.bitboards[BLACK_ROOK] |= 1 << 59

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
                    captured_idx = idx
                    break

        self.history.append(
            Undo(
                move,
                old_ep,
                captured_idx,
                cap_sq,
                prev_side,
                old_castling_rights,
            )
        )

        if captured_idx is not None:
            self.bitboards[captured_idx] ^= 1 << cap_sq

        target_idx = piece_idx
        if move.promotion:
            promo_map = PROMO_MAP_WHITE if piece_idx < 6 else PROMO_MAP_BLACK
            target_idx = promo_map[move.promotion]

        self.bitboards[target_idx] |= 1 << dst
        self.update_occupancies()
        self.side_to_move = BLACK if self.side_to_move == WHITE else WHITE

    def undo_move(self):
        undo = self.history.pop()
        move = undo.move
        src, dst = move.src, move.dst

        self.ep_square = undo.old_ep
        self.side_to_move = undo.prev_side
        self.castling_rights = undo.old_castling_rights

        if move.castling:
            if src == 4 and dst == 6:
                self.bitboards[WHITE_ROOK] ^= 1 << 5
                self.bitboards[WHITE_ROOK] |= 1 << 7
            elif src == 4 and dst == 2:
                self.bitboards[WHITE_ROOK] ^= 1 << 3
                self.bitboards[WHITE_ROOK] |= 1 << 0
            elif src == 60 and dst == 62:
                self.bitboards[BLACK_ROOK] ^= 1 << 61
                self.bitboards[BLACK_ROOK] |= 1 << 63
            elif src == 60 and dst == 58:
                self.bitboards[BLACK_ROOK] ^= 1 << 59
                self.bitboards[BLACK_ROOK] |= 1 << 56

        moved_idx = None

        for idx in range(12):
            if (self.bitboards[idx] >> dst) & 1:
                moved_idx = idx
                break
        assert moved_idx is not None

        self.bitboards[moved_idx] ^= 1 << dst
        if move.promotion:
            pawn_idx = WHITE_PAWN if moved_idx < 6 else BLACK_PAWN
            self.bitboards[pawn_idx] |= 1 << src
        else:
            self.bitboards[moved_idx] |= 1 << src

        if undo.captured_idx is not None:
            self.bitboards[undo.captured_idx] |= 1 << undo.cap_sq

        self.update_occupancies()
