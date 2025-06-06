from typing import List, Tuple, Optional

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
        self.history: List[Undo] = []
        self.raw_history: List[Tuple] = []

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

    def make_move(self, move: Move) -> None:
        """
        Execute `move` on the board. Steps are grouped into three phases:
          1) Remove all old bits
            (moving piece, captured piece, castling-rook if any)
          2) Update non-bitboard state
            (en passant, castling rights, push history)
          3) Place new bits (moved or promoted piece)
            and refresh occupancy/side
        """
        # ————— Phase 2a: Snapshot old state —————
        old_ep = self.ep_square
        prev_side = self.side_to_move
        old_castling = self.castling_rights
        # Clear en passant by default—only double-push can set a new one
        self.ep_square = None

        src, dst = move.src, move.dst

        # ————— Phase 2b: Identify which piece sits on src —————
        piece_idx = None
        for idx in range(12):
            if (self.bitboards[idx] & (1 << src)) != 0:
                piece_idx = idx
                break
        if piece_idx is None:
            raise ValueError(
                f"make_move: no piece found on source square {src}"
            )

        # ————— Phase 1b: Detect double‐pawn push → set new ep_square —————
        if piece_idx in (WHITE_PAWN, BLACK_PAWN):
            # Same file and two‐rank difference?
            if (dst % 8) == (src % 8) and abs((dst // 8) - (src // 8)) == 2:
                self.ep_square = (src + dst) // 2

        # ————— Phase 1c: Remove the moving piece from src —————
        self.bitboards[piece_idx] ^= 1 << src

        # ————— Phase 1d: Handle any capture (normal or en passant) —————
        captured_idx = None
        cap_sq: Optional[int] = None
        if move.capture:
            # If en passant capture, captured pawn is “behind” dst
            if (
                piece_idx in (WHITE_PAWN, BLACK_PAWN)
                and old_ep is not None
                and dst == old_ep
            ):
                cap_sq = dst - 8 if piece_idx == WHITE_PAWN else dst + 8
            else:
                cap_sq = dst

            # Find which piece‐type was on cap_sq
            for idx in range(12):
                if (self.bitboards[idx] >> cap_sq) & 1:
                    captured_idx = idx
                    break
            if captured_idx is None:
                raise ValueError(
                    f"make_move: no captured piece found on {cap_sq}"
                )

            # Remove that captured piece
            self.bitboards[captured_idx] ^= 1 << cap_sq

        # ———— Phase 2c: Update castling rights if
        # king/rook moved or rook captured ————
        if piece_idx == WHITE_KING:
            # King moved → White loses both castling rights
            self.castling_rights &= ~0b0011
        elif piece_idx == BLACK_KING:
            # King moved → Black loses both castling rights
            self.castling_rights &= ~0b1100

        # If a rook moved off a corner square, clear that side’s right
        if piece_idx in (WHITE_ROOK, BLACK_ROOK) and src in _CORNER_BIT:
            self.castling_rights &= ~(1 << _CORNER_BIT[src])

        # If a corner‐rook was captured, clear that side’s right
        if captured_idx in (WHITE_ROOK, BLACK_ROOK) and cap_sq in _CORNER_BIT:
            self.castling_rights &= ~(1 << _CORNER_BIT[cap_sq])

        # ————— Phase 2d: Record Undo object —————
        self.history.append(
            Undo(move, old_ep, captured_idx, cap_sq, prev_side, old_castling)
        )

        # ————— Phase 3a: Place the moved (or promoted) piece onto dst —————
        target_idx = piece_idx
        if move.promotion:
            promo_map = PROMO_MAP_WHITE if piece_idx < 6 else PROMO_MAP_BLACK
            target_idx = promo_map[move.promotion]
            # Ensure promotion is to a valid piece index
            assert target_idx in (
                WHITE_ROOK,
                BLACK_ROOK,
                WHITE_KNIGHT,
                BLACK_KNIGHT,
                WHITE_BISHOP,
                BLACK_BISHOP,
                WHITE_QUEEN,
                BLACK_QUEEN,
            )
        self.bitboards[target_idx] |= 1 << dst

        # ————— Phase 3b: Recompute occupancies and flip side to move —————
        self.update_occupancies()
        self.side_to_move = BLACK if self.side_to_move == WHITE else WHITE

    def undo_move(self) -> None:
        """
        Undo the last move. Steps are grouped in reverse:
          1) Restore flags (en passant, side, castling rights)
          2) Move castling rook back (if castling)
          3) Remove the moved or promoted piece from dst
          4) Restore pawn or move piece back to src
          5) Restore any captured piece
          6) Recompute occupancies
        """
        undo = self.history.pop()
        move = undo.move
        src, dst = move.src, move.dst

        # ————— Phase 1: Restore board‐state flags —————
        self.ep_square = undo.old_ep
        self.side_to_move = undo.prev_side
        self.castling_rights = undo.old_castling_rights

        # ————— Phase 2: Undo castling’s rook (if castling) —————
        if move.castling:
            if src == 4 and dst == 6:
                # White kingside: move rook f1→h1
                self.bitboards[WHITE_ROOK] ^= 1 << 5
                self.bitboards[WHITE_ROOK] |= 1 << 7
            elif src == 4 and dst == 2:
                # White queenside: move rook d1→a1
                self.bitboards[WHITE_ROOK] ^= 1 << 3
                self.bitboards[WHITE_ROOK] |= 1 << 0
            elif src == 60 and dst == 62:
                # Black kingside: move rook f8→h8
                self.bitboards[BLACK_ROOK] ^= 1 << 61
                self.bitboards[BLACK_ROOK] |= 1 << 63
            elif src == 60 and dst == 58:
                # Black queenside: move rook d8→a8
                self.bitboards[BLACK_ROOK] ^= 1 << 59
                self.bitboards[BLACK_ROOK] |= 1 << 56

        # ————— Phase 3: Remove the moved/promoted piece from dst —————
        moved_idx: Optional[int] = None
        for idx in range(12):
            if (self.bitboards[idx] >> dst) & 1:
                moved_idx = idx
                break
        if moved_idx is None:
            raise ValueError(
                f"undo_move: no piece found on destination square {dst}"
            )
        self.bitboards[moved_idx] ^= 1 << dst

        # ————— Phase 4: Restore pawn (if promo) or move piece back to src ————— # noqa:E501
        if move.promotion:
            # If promoted, restore a pawn on src
            pawn_idx = WHITE_PAWN if moved_idx < 6 else BLACK_PAWN
            self.bitboards[pawn_idx] |= 1 << src
        else:
            # Otherwise, move the same piece back to src
            self.bitboards[moved_idx] |= 1 << src

        # ——— Phase 5: Restore any captured piece at cap_sq —————
        if undo.captured_idx is not None:
            self.bitboards[undo.captured_idx] |= 1 << undo.cap_sq

        # ————— Phase 6: Recompute occupancies —————
        self.update_occupancies()

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
        self.ep_square = 0

        # 2) Figure out which piece is on src
        piece_idx = None
        for idx in range(12):
            if (self.bitboards[idx] >> src) & 1:
                piece_idx = idx
                break
        if piece_idx is None:
            raise ValueError(f"make_move_raw: no piece at src={src}")

        # 3) Handle double‐pawn push (pawn ep target)
        if piece_idx in (WHITE_PAWN, BLACK_PAWN):
            rank_diff = (dst // 8) - (src // 8)
            if abs(rank_diff) == 2:
                # set ep target square
                self.ep_square = (src + dst) // 2

        # 4) Remove the moving piece from src
        self.bitboards[piece_idx] ^= 1 << src

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

            for idx in range(12):
                if (self.bitboards[idx] >> cap_sq) & 1:
                    captured_idx = idx
                    break
            if captured_idx is None:
                raise ValueError(
                    f"make_move_raw: no captured piece on {cap_sq}"
                )
            # remove captured piece
            self.bitboards[captured_idx] ^= 1 << cap_sq

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
                self.bitboards[WHITE_ROOK] ^= 1 << 7
                self.bitboards[WHITE_ROOK] |= 1 << 5
            elif piece_idx == WHITE_KING and src == 4 and dst == 2:
                # White queenside: rook 0→3
                self.bitboards[WHITE_ROOK] ^= 1 << 0
                self.bitboards[WHITE_ROOK] |= 1 << 3
            elif piece_idx == BLACK_KING and src == 60 and dst == 62:
                # Black kingside: rook 63→61
                self.bitboards[BLACK_ROOK] ^= 1 << 63
                self.bitboards[BLACK_ROOK] |= 1 << 61
            elif piece_idx == BLACK_KING and src == 60 and dst == 58:
                # Black queenside: rook 56→59
                self.bitboards[BLACK_ROOK] ^= 1 << 56
                self.bitboards[BLACK_ROOK] |= 1 << 59

        # 8) Place the moving (or promoted) piece on dst
        target_idx = piece_idx
        if promotion:
            # promotion_map chooses new piece‐index from "Q"/"R"/"B"/"N"
            promo_map = PROMO_MAP_WHITE if piece_idx < 6 else PROMO_MAP_BLACK
            target_idx = promo_map[promotion]
        self.bitboards[target_idx] |= 1 << dst

        # 9) Recompute occupancy and flip side
        self.update_occupancies()
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
            )
        )

    def undo_move_raw(self) -> None:
        """
        Reverse exactly what make_move_raw did, by popping raw_history.
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
        ) = self.raw_history.pop()

        # 1) Restore ep, side, castling flags
        self.ep_square = old_ep
        self.side_to_move = prev_side
        self.castling_rights = old_castling

        # 2) If castling, move rook back
        if castling:
            if src == 4 and dst == 6:
                # White kingside: rook 5→7
                self.bitboards[WHITE_ROOK] ^= 1 << 5
                self.bitboards[WHITE_ROOK] |= 1 << 7
            elif src == 4 and dst == 2:
                # White queenside: rook 3→0
                self.bitboards[WHITE_ROOK] ^= 1 << 3
                self.bitboards[WHITE_ROOK] |= 1 << 0
            elif src == 60 and dst == 62:
                # Black kingside: rook 61→63
                self.bitboards[BLACK_ROOK] ^= 1 << 61
                self.bitboards[BLACK_ROOK] |= 1 << 63
            elif src == 60 and dst == 58:
                # Black queenside: rook 59→56
                self.bitboards[BLACK_ROOK] ^= 1 << 59
                self.bitboards[BLACK_ROOK] |= 1 << 56

        # 3) Remove the moved (or promoted) piece from dst
        moved_idx = None
        for i in range(12):
            if (self.bitboards[i] >> dst) & 1:
                moved_idx = i
                break
        if moved_idx is None:
            raise ValueError(f"undo_move_raw: no piece found on dst={dst}")
        self.bitboards[moved_idx] ^= 1 << dst

        # 4) If it was a promotion,
        # restore the pawn; else move piece back to src
        if promotion:
            pawn_idx = WHITE_PAWN if moved_idx < 6 else BLACK_PAWN
            self.bitboards[pawn_idx] |= 1 << src
        else:
            self.bitboards[moved_idx] |= 1 << src

        # 5) Restore captured piece, if any
        if captured_idx is not None:
            self.bitboards[captured_idx] |= 1 << cap_sq

        # 6) Recompute occupancy
        self.update_occupancies()
