# from engine.bitboard.config import RawMove  # noqa: TC002
from typing import List, Tuple, Optional
from engine.bitboard.attack_utils import (
    is_square_attacked as _is_square_attacked,
)
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

_CORNER_BIT = {0: 1, 7: 0, 56: 3, 63: 2}


class Board:
    def __init__(self):
        # a list of 12 ints, one per piece-type
        self.bitboards = [0] * 12

        # stored occupancy bitboards
        self.white_occ = 0
        self.black_occ = 0
        self.all_occ = 0

        # En_passant flag/square
        self.ep_square: Optional[int] = None

        # History of all moves
        self.raw_history: List[Tuple] = []

        # Move counts half and full
        self.halfmove_clock = 0  # counts plies since last pawn move or capture
        self.fullmove_number = 1  # starts at 1, increments after Black’s turn

        # Flag to see side to move
        self.side_to_move = WHITE

        # Castling rights
        self.castling_rights: int = 0

        # create an empty lookup from 0..63 -> piece‐index or None
        self.square_to_piece: list[Optional[int]] = [None] * 64

        # Initialize starting positions
        self.init_positions()

        # build the square‐to‐piece map based on INITIAL_MASKS
        for idx in range(12):
            bb = self.bitboards[idx]
            while bb:
                lsb = bb & -bb
                sq = lsb.bit_length() - 1
                self.square_to_piece[sq] = idx
                bb ^= lsb

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

    def make_move_raw(
        self, raw_move: tuple[int, int, bool, Optional[str], bool, bool]
    ) -> None:
        """
        Exactly the same sequence as make_move(Move(...)),
        but unpack from a 6‐tuple instead of a Move object,
        and push a minimal “raw” undo record into self.raw_history.
        """
        # print(raw_move)
        src, dst, capture, promotion, en_passant, castling = raw_move

        # 1) Snapshot previous state
        old_ep = self.ep_square
        prev_side = self.side_to_move
        old_castling = self.castling_rights
        self.ep_square = None

        # 2) Figure out which piece is on src
        piece_idx = self.square_to_piece[src]
        if piece_idx is None:
            raise ValueError(f"Expected a piece on {src}")

        # 3) Handle double‐pawn push (pawn ep target)
        if piece_idx in (WHITE_PAWN, BLACK_PAWN):
            rank_diff = (dst // 8) - (src // 8)
            if abs(rank_diff) == 2 and not capture:
                self.ep_square = (src + dst) // 2

        # 4) Remove the moving piece from src
        self.bitboards[piece_idx] ^= 1 << src
        self.square_to_piece[src] = None
        if piece_idx < 6:
            # white pawn/knight/bishop/rook/queen/king moved
            self.white_occ ^= 1 << src
        else:
            # black piece moved
            self.black_occ ^= 1 << src

        # 5) Handle capture (including en passant)
        captured_idx = None
        cap_sq = None
        if capture:
            # en passant capture?
            if (
                piece_idx in (WHITE_PAWN, BLACK_PAWN)
                and old_ep
                and dst == old_ep
            ):
                cap_sq = dst - 8 if piece_idx == WHITE_PAWN else dst + 8
            else:
                cap_sq = dst

            captured_idx = self.square_to_piece[cap_sq]
            if captured_idx is None:
                raise ValueError(
                    f"make_move_raw: no captured piece at {cap_sq}"
                )
            # remove captured piece
            self.bitboards[captured_idx] ^= 1 << cap_sq
            self.square_to_piece[cap_sq] = None
            if captured_idx < 6:
                self.white_occ ^= 1 << cap_sq
            else:
                self.black_occ ^= 1 << cap_sq

        if piece_idx in (WHITE_PAWN, BLACK_PAWN) or capture:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # 6) Update castling rights if moving king or rook
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

        # 7) Handle castling rook move
        if castling:
            if piece_idx == WHITE_KING and src == 4 and dst == 6:
                # White kingside: rook 7→5
                # remove rook from 7
                self.bitboards[WHITE_ROOK] ^= 1 << 7
                self.square_to_piece[7] = None
                self.white_occ ^= 1 << 7
                # put rook on 5
                self.bitboards[WHITE_ROOK] |= 1 << 5
                self.square_to_piece[5] = WHITE_ROOK
                self.white_occ |= 1 << 5

            elif piece_idx == WHITE_KING and src == 4 and dst == 2:
                # White queenside: rook 0→3
                self.bitboards[WHITE_ROOK] ^= 1 << 0
                self.square_to_piece[0] = None
                self.white_occ ^= 1 << 0
                self.bitboards[WHITE_ROOK] |= 1 << 3
                self.square_to_piece[3] = WHITE_ROOK
                self.white_occ |= 1 << 3

            elif piece_idx == BLACK_KING and src == 60 and dst == 62:
                # Black kingside: rook 63→61
                self.bitboards[BLACK_ROOK] ^= 1 << 63
                self.square_to_piece[63] = None
                self.black_occ ^= 1 << 63
                self.bitboards[BLACK_ROOK] |= 1 << 61
                self.square_to_piece[61] = BLACK_ROOK
                self.black_occ |= 1 << 61

            elif piece_idx == BLACK_KING and src == 60 and dst == 58:
                # Black queenside: rook 56→59
                self.bitboards[BLACK_ROOK] ^= 1 << 56
                self.square_to_piece[56] = None
                self.black_occ ^= 1 << 56
                self.bitboards[BLACK_ROOK] |= 1 << 59
                self.square_to_piece[59] = BLACK_ROOK
                self.black_occ |= 1 << 59

        # 8) Place the moving (or promoted) piece on dst
        target_idx = piece_idx
        if promotion:
            # promotion_map chooses new piece‐index from "Q"/"R"/"B"/"N"
            promo_map = PROMO_MAP_WHITE if piece_idx < 6 else PROMO_MAP_BLACK
            target_idx = promo_map[promotion]

        self.bitboards[target_idx] |= 1 << dst
        self.square_to_piece[dst] = target_idx
        if target_idx < 6:
            self.white_occ |= 1 << dst
        else:
            self.black_occ |= 1 << dst

        # 9) Recompute occupancy, update full move, and flip side
        self.all_occ = self.white_occ | self.black_occ

        if self.side_to_move == BLACK:
            self.fullmove_number += 1

        self.side_to_move = BLACK if self.side_to_move == WHITE else WHITE

        # 10) Push a “raw history” tuple so
        # undo_move_raw can restore everything
        self.raw_history.append(
            (
                piece_idx,
                src,
                dst,
                captured_idx,
                cap_sq,
                old_ep,
                prev_side,
                old_castling,
                promotion,
                en_passant,
                castling,
                self.halfmove_clock,
                self.fullmove_number,
            )
        )

    def undo_move_raw(self) -> None:
        """
        Reverse exactly what make_move_raw did, by popping raw_history.
        Now uses O(1) occupancy updates + square_to_piece lookups.
        """
        (
            piece_idx,
            src,
            dst,
            captured_idx,
            cap_sq,
            old_ep,
            prev_side,
            old_castling,
            promotion,
            en_passant,
            castling,
            old_halfmove,
            old_fullmove,
        ) = self.raw_history.pop()

        # 1) Restore ep, side, castling flags, and move clocks
        self.halfmove_clock = old_halfmove
        self.fullmove_number = old_fullmove
        self.ep_square = old_ep
        self.side_to_move = prev_side
        self.castling_rights = old_castling

        # 2) If castling, move rook back (undo the two‐square rook relocation)
        if castling:
            # White kingside: rook was 7→5; undo: move 5→7
            if src == 4 and dst == 6:
                self.bitboards[WHITE_ROOK] ^= 1 << 5
                self.square_to_piece[5] = None
                self.white_occ ^= 1 << 5

                self.bitboards[WHITE_ROOK] |= 1 << 7
                self.square_to_piece[7] = WHITE_ROOK
                self.white_occ |= 1 << 7

            # White queenside: rook was 0→3; undo: move 3→0
            elif src == 4 and dst == 2:
                self.bitboards[WHITE_ROOK] ^= 1 << 3
                self.square_to_piece[3] = None
                self.white_occ ^= 1 << 3

                self.bitboards[WHITE_ROOK] |= 1 << 0
                self.square_to_piece[0] = WHITE_ROOK
                self.white_occ |= 1 << 0

            # Black kingside: rook was 63→61; undo: move 61→63
            elif src == 60 and dst == 62:
                self.bitboards[BLACK_ROOK] ^= 1 << 61
                self.square_to_piece[61] = None
                self.black_occ ^= 1 << 61

                self.bitboards[BLACK_ROOK] |= 1 << 63
                self.square_to_piece[63] = BLACK_ROOK
                self.black_occ |= 1 << 63

            # Black queenside: rook was 56→59; undo: move 59→56
            elif src == 60 and dst == 58:
                self.bitboards[BLACK_ROOK] ^= 1 << 59
                self.square_to_piece[59] = None
                self.black_occ ^= 1 << 59

                self.bitboards[BLACK_ROOK] |= 1 << 56
                self.square_to_piece[56] = BLACK_ROOK
                self.black_occ |= 1 << 56

        # 3) Remove the moved (or promoted) piece from dst
        moved_idx = self.square_to_piece[dst]
        if moved_idx is None:
            raise ValueError(f"undo_move_raw: no piece found on dst={dst}")
        # Remove that bit
        self.bitboards[moved_idx] ^= 1 << dst
        self.square_to_piece[dst] = None
        if moved_idx < 6:
            self.white_occ ^= 1 << dst
        else:
            self.black_occ ^= 1 << dst

        # 4) If it was a promotion, put back a pawn on src;
        #    else move piece back to src
        if promotion:
            pawn_idx = WHITE_PAWN if moved_idx < 6 else BLACK_PAWN
            self.bitboards[pawn_idx] |= 1 << src
            self.square_to_piece[src] = pawn_idx
            if pawn_idx < 6:
                self.white_occ |= 1 << src
            else:
                self.black_occ |= 1 << src
        else:
            # “moved_idx” is the same as piece_idx if no promotion
            self.bitboards[moved_idx] |= 1 << src
            self.square_to_piece[src] = moved_idx
            if moved_idx < 6:
                self.white_occ |= 1 << src
            else:
                self.black_occ |= 1 << src

        # 5) Restore captured piece, if any
        if captured_idx is not None:
            self.bitboards[captured_idx] |= 1 << cap_sq
            self.square_to_piece[cap_sq] = captured_idx
            if captured_idx < 6:
                self.white_occ |= 1 << cap_sq
            else:
                self.black_occ |= 1 << cap_sq

        # 6) NO LONGER recompute occupancies from scratch—just OR white+black
        self.all_occ = self.white_occ | self.black_occ
