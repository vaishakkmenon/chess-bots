# engine/bitboard/board.py

from typing import List, Optional
from engine.bitboard.config import RawHistoryEntry  # noqa : TC001
from engine.bitboard.attack_utils import (
    is_square_attacked as _is_square_attacked,
)
from engine.bitboard.utils import algebraic_to_index, index_to_algebraic
from engine.bitboard.constants import (
    INITIAL_MASKS,
    PIECE_MAP,
    INV_PIECE_MAP,
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
    CASTLE_WHITE_KINGSIDE,
    CASTLE_WHITE_QUEENSIDE,
    CASTLE_BLACK_KINGSIDE,
    CASTLE_BLACK_QUEENSIDE,
    CASTLE_ALL,
    ZOBRIST_PIECE_KEYS,
    ZOBRIST_SIDE_KEY,
    ZOBRIST_CASTLE_KEYS,
    ZOBRIST_EP_KEYS,
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

castle_map = {
    CASTLE_WHITE_KINGSIDE: ZOBRIST_CASTLE_KEYS["K"],
    CASTLE_WHITE_QUEENSIDE: ZOBRIST_CASTLE_KEYS["Q"],
    CASTLE_BLACK_KINGSIDE: ZOBRIST_CASTLE_KEYS["k"],
    CASTLE_BLACK_QUEENSIDE: ZOBRIST_CASTLE_KEYS["q"],
}


class Board:

    bitboards: List[int]
    white_occ: int
    black_occ: int
    all_occ: int
    ep_square: Optional[int]
    raw_history: List[RawHistoryEntry]  # Raw history records
    halfmove_clock: int
    fullmove_number: int
    side_to_move: int
    castling_rights: int
    square_to_piece: List[Optional[int]]
    zobrist_key: int
    zobrist_history: List[int]

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
        self.raw_history = []

        # Move counts half and full
        self.halfmove_clock = 0  # counts plies since last pawn move or capture
        self.fullmove_number = 1  # starts at 1, increments after Black’s turn

        # Flag to see side to move
        self.side_to_move = WHITE

        # Castling rights
        self.castling_rights: int = 0

        # create an empty lookup from 0..63 -> piece‐index or None
        self.square_to_piece: List[Optional[int]] = [None] * 64

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
        rows: List[str] = []
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
        # All castling rights at start
        self.castling_rights = CASTLE_ALL

        # Compute starting board zobrist key
        self._compute_zobrist_from_scratch()

        # Keep a history of zobrist keys for repetition checks
        # Also used for testing purposes
        self.zobrist_history = [self.zobrist_key]

    def _compute_zobrist_from_scratch(self) -> None:
        key = 0
        # Piece XOR for all pieces
        for piece_idx in range(12):
            bb = self.bitboards[piece_idx]
            while bb:
                lsb = bb & -bb
                sq = lsb.bit_length() - 1
                key ^= ZOBRIST_PIECE_KEYS[piece_idx][sq]
                bb ^= lsb
        # Side to move changes with black
        if self.side_to_move == BLACK:
            key ^= ZOBRIST_SIDE_KEY

        # XOR each of the keys for all castling types
        for mask, zob_key in castle_map.items():
            if self.castling_rights & mask:
                key ^= zob_key

        # XOR for the file that en-passant is happening
        if self.ep_square is not None:
            file = self.ep_square % 8
            key ^= ZOBRIST_EP_KEYS[file]

        self.zobrist_key = key

    def get_piece_char(self, square: int) -> Optional[str]:
        """
        Return the piece character on the given square, or None if empty.
        E.g. 'N' for a white knight, 'q' for a black queen.
        """
        idx = self.square_to_piece[square]
        return INV_PIECE_MAP[idx] if idx is not None else None

    def set_fen(self, fen: str) -> None:
        """
        Parse a FEN string and update the board state:
          - self.bitboards
          - self.side_to_move
          - self.castling_rights
          - self.ep_square
          - self.halfmove_clock
          - self.fullmove_number
        Then rebuild occupancies and square_to_piece.
        """
        parts = fen.strip().split()
        if len(parts) != 6:
            raise ValueError(f"Invalid FEN (must have 6 fields): {fen}")
        placement, side, castle, ep, half, full = parts

        # 1) Clear bitboards
        self.bitboards = [0] * 12

        # 2) Parse piece placement
        rows = placement.split("/")
        if len(rows) != 8:
            raise ValueError(f"Invalid FEN placement: {placement}")
        for rank_idx, row in enumerate(rows):
            file = 0
            rank = 7 - rank_idx
            for ch in row:
                if ch.isdigit():
                    file += int(ch)
                else:
                    if ch not in PIECE_MAP:
                        raise ValueError(f"Invalid FEN piece char: {ch}")
                    idx = PIECE_MAP[ch]
                    sq = rank * 8 + file
                    self.bitboards[idx] |= 1 << sq
                    file += 1
            if file != 8:
                raise ValueError("Invalid FEN placement")

        # Side to move
        if side == "w":
            self.side_to_move = WHITE
        elif side == "b":
            self.side_to_move = BLACK
        else:
            raise ValueError(f"Invalid FEN side-to-move: {side}")

        # Castling rights
        self.castling_rights = 0
        if "K" in castle:
            self.castling_rights |= CASTLE_WHITE_KINGSIDE
        if "Q" in castle:
            self.castling_rights |= CASTLE_WHITE_QUEENSIDE
        if "k" in castle:
            self.castling_rights |= CASTLE_BLACK_KINGSIDE
        if "q" in castle:
            self.castling_rights |= CASTLE_BLACK_QUEENSIDE

        # 5) En-passant square
        if ep == "-" or ep == "":
            self.ep_square = None
        else:
            self.ep_square = algebraic_to_index(ep)

        # 6) Half-move and full-move counters
        try:
            self.halfmove_clock = int(half)
            self.fullmove_number = int(full)
        except ValueError:
            raise ValueError(
                f"Invalid FEN move counters: half={half}, full={full}"
            )

        # 7) Rebuild occupancies
        self.update_occupancies()

        # 8) Rebuild square_to_piece map
        self.square_to_piece = [None] * 64
        for idx, bb in enumerate(self.bitboards):
            b = bb
            while b:
                lsb = b & -b
                sq = lsb.bit_length() - 1
                self.square_to_piece[sq] = idx
                b ^= lsb

    def get_fen(self) -> str:
        """
        Serialize current board state into a FEN string.
        """
        # 1) Piece-placement
        rows: List[str] = []
        for rank in range(7, -1, -1):
            empty = 0
            row_s: List[str] = []
            for file in range(8):
                sq = rank * 8 + file
                idx = self.square_to_piece[sq]
                if idx is None:
                    empty += 1
                else:
                    if empty:
                        row_s.append(str(empty))
                        empty = 0
                    row_s.append(INV_PIECE_MAP[idx])
            if empty:
                row_s.append(str(empty))
            rows.append("".join(row_s))
        placement = "/".join(rows)

        # Side to move
        side = "w" if self.side_to_move == WHITE else "b"

        # Castling
        cr = self.castling_rights
        castle = (
            ("K" if cr & CASTLE_WHITE_KINGSIDE else "")
            + ("Q" if cr & CASTLE_WHITE_QUEENSIDE else "")
            + ("k" if cr & CASTLE_BLACK_KINGSIDE else "")
            + ("q" if cr & CASTLE_BLACK_QUEENSIDE else "")
        ) or "-"

        # En-passant
        ep = (
            "-"
            if self.ep_square is None
            else index_to_algebraic(self.ep_square)
        )

        # Halfmove & fullmove
        half = str(self.halfmove_clock)
        full = str(self.fullmove_number)

        return f"{placement} {side} {castle} {ep} {half} {full}"

    def update_occupancies(self):
        """Recompute white_occ, black_occ, and all_occ from self.bitboards."""
        w = 0
        for i in range(6):
            w |= self.bitboards[i]
        self.white_occ = w
        b = 0
        for i in range(6, 12):
            b |= self.bitboards[i]
        self.black_occ = b
        self.all_occ = self.white_occ | self.black_occ

    def is_square_attacked(self, square: int, attacker_side: int) -> bool:
        return _is_square_attacked(self, square, attacker_side)

    def in_check(self, side: int) -> bool:
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
        src, dst, capture, promotion, en_passant, castling = raw_move

        old_ep = self.ep_square
        prev_side = self.side_to_move
        old_castling = self.castling_rights
        self.ep_square = None

        piece_idx = self.square_to_piece[src]
        if piece_idx is None:
            raise ValueError(f"Expected a piece on {src}")

        # double-pawn push
        if piece_idx in (WHITE_PAWN, BLACK_PAWN):
            rank_diff = (dst // 8) - (src // 8)
            if abs(rank_diff) == 2 and not capture:
                self.ep_square = (src + dst) // 2

        # remove from src
        self.zobrist_key ^= ZOBRIST_PIECE_KEYS[piece_idx][src]
        self.bitboards[piece_idx] ^= 1 << src
        self.square_to_piece[src] = None
        if piece_idx < 6:
            self.white_occ ^= 1 << src
        else:
            self.black_occ ^= 1 << src

        # capture
        captured_idx = None
        cap_sq = None
        if capture:
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
            self.zobrist_key ^= ZOBRIST_PIECE_KEYS[captured_idx][cap_sq]
            self.bitboards[captured_idx] ^= 1 << cap_sq
            self.square_to_piece[cap_sq] = None
            if captured_idx < 6:
                self.white_occ ^= 1 << cap_sq
            else:
                self.black_occ ^= 1 << cap_sq

        # halfmove clock
        if piece_idx in (WHITE_PAWN, BLACK_PAWN) or capture:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # If there was an old ep square, XOR out its file key:
        if old_ep is not None:
            self.zobrist_key ^= ZOBRIST_EP_KEYS[old_ep % 8]
        # If a new ep square got set, XOR in its file key:
        if self.ep_square is not None:
            self.zobrist_key ^= ZOBRIST_EP_KEYS[self.ep_square % 8]

        # update castling rights for king/rook moves
        if piece_idx == WHITE_KING:
            # clears both White rights
            self.castling_rights &= ~(
                CASTLE_WHITE_KINGSIDE | CASTLE_WHITE_QUEENSIDE
            )
        elif piece_idx == BLACK_KING:
            # clears both Black rights
            self.castling_rights &= ~(
                CASTLE_BLACK_KINGSIDE | CASTLE_BLACK_QUEENSIDE
            )
        elif piece_idx == WHITE_ROOK:
            # Rook move clears the *correct* White side depending on src:
            if src == 0:  # a1
                self.castling_rights &= ~CASTLE_WHITE_KINGSIDE
            elif src == 7:  # h1
                self.castling_rights &= ~CASTLE_WHITE_QUEENSIDE
        elif piece_idx == BLACK_ROOK:
            # Similarly for Black rooks:
            if src == 56:  # a8
                self.castling_rights &= ~CASTLE_BLACK_KINGSIDE
            elif src == 63:  # h8
                self.castling_rights &= ~CASTLE_BLACK_QUEENSIDE

        # castling rook move
        if castling:
            # white kingside
            if piece_idx == WHITE_KING and src == 4 and dst == 6:
                self.bitboards[WHITE_ROOK] ^= 1 << 7
                self.square_to_piece[7] = None
                self.white_occ ^= 1 << 7
                self.bitboards[WHITE_ROOK] |= 1 << 5
                self.square_to_piece[5] = WHITE_ROOK
                self.white_occ |= 1 << 5
            # white queenside
            elif piece_idx == WHITE_KING and src == 4 and dst == 2:
                self.bitboards[WHITE_ROOK] ^= 1 << 0
                self.square_to_piece[0] = None
                self.white_occ ^= 1 << 0
                self.bitboards[WHITE_ROOK] |= 1 << 3
                self.square_to_piece[3] = WHITE_ROOK
                self.white_occ |= 1 << 3
            # black kingside
            elif piece_idx == BLACK_KING and src == 60 and dst == 62:
                self.bitboards[BLACK_ROOK] ^= 1 << 63
                self.square_to_piece[63] = None
                self.black_occ ^= 1 << 63
                self.bitboards[BLACK_ROOK] |= 1 << 61
                self.square_to_piece[61] = BLACK_ROOK
                self.black_occ |= 1 << 61
            # black queenside
            elif piece_idx == BLACK_KING and src == 60 and dst == 58:
                self.bitboards[BLACK_ROOK] ^= 1 << 56
                self.square_to_piece[56] = None
                self.black_occ ^= 1 << 56
                self.bitboards[BLACK_ROOK] |= 1 << 59
                self.square_to_piece[59] = BLACK_ROOK
                self.black_occ |= 1 << 59

        if old_castling != self.castling_rights:
            # remove any old castling bits
            for mask, zob_key in castle_map.items():
                if old_castling & mask:
                    self.zobrist_key ^= zob_key
            # add any new castling bits
            for mask, zob_key in castle_map.items():
                if self.castling_rights & mask:
                    self.zobrist_key ^= zob_key

        target_idx = piece_idx
        if promotion:
            promo_map = PROMO_MAP_WHITE if piece_idx < 6 else PROMO_MAP_BLACK
            target_idx = promo_map[promotion]

        self.zobrist_key ^= ZOBRIST_PIECE_KEYS[target_idx][dst]
        self.bitboards[target_idx] |= 1 << dst
        self.square_to_piece[dst] = target_idx
        if target_idx < 6:
            self.white_occ |= 1 << dst
        else:
            self.black_occ |= 1 << dst

        # update occupancy, fullmove, and side
        self.all_occ = self.white_occ | self.black_occ
        if self.side_to_move == BLACK:
            self.fullmove_number += 1
        self.side_to_move = BLACK if self.side_to_move == WHITE else WHITE
        self.zobrist_key ^= ZOBRIST_SIDE_KEY

        self.zobrist_history.append(self.zobrist_key)
        # push raw history record
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

        self.halfmove_clock = old_halfmove
        self.fullmove_number = old_fullmove
        self.ep_square = old_ep
        self.side_to_move = prev_side
        self.castling_rights = old_castling

        self.zobrist_history.pop()
        self.zobrist_key = self.zobrist_history[-1]

        if castling:
            if src == 4 and dst == 6:
                self.bitboards[WHITE_ROOK] ^= 1 << 5
                self.square_to_piece[5] = None
                self.white_occ ^= 1 << 5
                self.bitboards[WHITE_ROOK] |= 1 << 7
                self.square_to_piece[7] = WHITE_ROOK
                self.white_occ |= 1 << 7
            elif src == 4 and dst == 2:
                self.bitboards[WHITE_ROOK] ^= 1 << 3
                self.square_to_piece[3] = None
                self.white_occ ^= 1 << 3
                self.bitboards[WHITE_ROOK] |= 1 << 0
                self.square_to_piece[0] = WHITE_ROOK
                self.white_occ |= 1 << 0
            elif src == 60 and dst == 62:
                self.bitboards[BLACK_ROOK] ^= 1 << 61
                self.square_to_piece[61] = None
                self.black_occ ^= 1 << 61
                self.bitboards[BLACK_ROOK] |= 1 << 63
                self.square_to_piece[63] = BLACK_ROOK
                self.black_occ |= 1 << 63
            elif src == 60 and dst == 58:
                self.bitboards[BLACK_ROOK] ^= 1 << 59
                self.square_to_piece[59] = None
                self.black_occ ^= 1 << 59
                self.bitboards[BLACK_ROOK] |= 1 << 56
                self.square_to_piece[56] = BLACK_ROOK
                self.black_occ |= 1 << 56

        # ====== now the real undo of the moved piece ======

        if promotion:
            # 1) clear the promoted piece off dst
            promo_map = PROMO_MAP_WHITE if piece_idx < 6 else PROMO_MAP_BLACK
            promo_idx = promo_map[promotion]
            self.bitboards[promo_idx] ^= 1 << dst
            self.square_to_piece[dst] = None
            if promo_idx < 6:
                self.white_occ ^= 1 << dst
            else:
                self.black_occ ^= 1 << dst

            # 2) restore exactly one pawn on src
            pawn_idx = WHITE_PAWN if piece_idx < 6 else BLACK_PAWN
            self.bitboards[pawn_idx] |= 1 << src
            self.square_to_piece[src] = pawn_idx
            if pawn_idx < 6:
                self.white_occ |= 1 << src
            else:
                self.black_occ |= 1 << src

        else:
            # normal, non‐promotion undo: move piece_idx from dst back to src
            self.bitboards[piece_idx] ^= 1 << dst
            self.square_to_piece[dst] = None
            if piece_idx < 6:
                self.white_occ ^= 1 << dst
            else:
                self.black_occ ^= 1 << dst

            self.bitboards[piece_idx] |= 1 << src
            self.square_to_piece[src] = piece_idx
            if piece_idx < 6:
                self.white_occ |= 1 << src
            else:
                self.black_occ |= 1 << src

        # ====== finally, if there was a capture, put it back ======
        if captured_idx is not None:
            if en_passant:
                restore_sq = dst - 8 if prev_side == WHITE else dst + 8
            else:
                assert cap_sq is not None
                restore_sq = cap_sq  # guaranteed non‐None
            self.bitboards[captured_idx] |= 1 << restore_sq
            self.square_to_piece[restore_sq] = captured_idx
            if captured_idx < 6:
                self.white_occ |= 1 << restore_sq
            else:
                self.black_occ |= 1 << restore_sq

        # and rebuild the all‐occupancy
        self.all_occ = self.white_occ | self.black_occ
