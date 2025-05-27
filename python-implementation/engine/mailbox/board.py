from __future__ import annotations
from typing import Optional, Tuple, List, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.mailbox.zobrist import Zobrist
    from engine.mailbox.moves.move import Move


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

    # ──────────────────────────────────────────────────────────────
    # Convenience sets
    # ──────────────────────────────────────────────────────────────

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

    @staticmethod
    def uci(move: Move) -> str:
        files = "abcdefgh"
        f0, r0 = move.from_sq
        f1, r1 = move.to_sq
        return f"{files[f0-1]}{r0}{files[f1-1]}{r1}"

    # ──────────────────────────────────────────────────────────────
    # Construction helpers
    # ──────────────────────────────────────────────────────────────

    def _to_idx(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert (file, rank) → 0‑based [rank][file] indices."""
        file, rank = pos
        return rank - 1, file - 1

    def __getitem__(self, pos: Tuple[int, int]) -> str:
        r, c = self._to_idx(pos)
        return self.squares[r][c]

    def __setitem__(self, pos: Tuple[int, int], piece: str):
        r, c = self._to_idx(pos)
        self.squares[r][c] = piece

    # ──────────────────────────────────────────────────────────────
    # Boiler‑plate predicates
    # ──────────────────────────────────────────────────────────────

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

    # ──────────────────────────────────────────────────────────────
    # Core life‑cycle
    # ──────────────────────────────────────────────────────────────

    def __init__(self, zobrist: "Zobrist"):
        self.zobrist = zobrist

        # 0‑based "rank × file" grid
        self.squares = [
            [self.EMPTY for _ in range(self.FILES)] for _ in range(self.RANKS)
        ]

        # clocks & game‑state flags
        self.halfmove_clock = 0
        self.fullmove_number = 1

        self.en_passant_target: Optional[Tuple[int, int]] = None
        self.white_can_castle_kingside = True
        self.white_can_castle_queenside = True
        self.black_can_castle_kingside = True
        self.black_can_castle_queenside = True

        self.side_to_move = "white"

        # initial empty‑board hash
        self.zobrist_hash = self.zobrist.compute_hash(self, self.side_to_move)
        self.history: List[int] = [self.zobrist_hash]

    # ──────────────────────────────────────────────────────────────
    # Pretty‑print
    # ──────────────────────────────────────────────────────────────

    def __str__(self) -> str:
        rows = []
        for rank_no in range(self.RANKS, 0, -1):
            row = self.squares[rank_no - 1]
            rows.append(f"{rank_no}| " + " ".join(row))
        rows.append(" |" + "-" * (self.FILES * 2 - 1))
        rows.append("   " + " ".join("abcdefgh"[: self.FILES]))
        return "\n".join(rows)

    # ──────────────────────────────────────────────────────────────
    # Set‑up helpers
    # ──────────────────────────────────────────────────────────────

    def init_positions(self) -> None:
        """Standard starting position and fresh Zobrist hash."""
        for r in range(self.RANKS):
            for c in range(self.FILES):
                self.squares[r][c] = self.EMPTY

        # pawns
        for file in range(1, self.FILES + 1):
            self[(file, 2)] = self.PIECES["WP"]
            self[(file, 7)] = self.PIECES["BP"]

        # back‑rank
        order = "RNBQKBNR"
        for file, code in enumerate(order, 1):
            self[(file, 1)] = self.PIECES[f"W{code}"]
            self[(file, 8)] = self.PIECES[f"B{code}"]

        # reset state flags
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.en_passant_target = None
        self.side_to_move = "white"
        self.white_can_castle_kingside = self.white_can_castle_queenside = True
        self.black_can_castle_kingside = self.black_can_castle_queenside = True

        self.zobrist_hash = self.zobrist.compute_hash(self, self.side_to_move)
        self.history = [self.zobrist_hash]

    def set_fen(self, fen: str) -> None:
        """
        Load a full FEN string, parsing:
         1) piece placement
         2) side to move
         3) castling rights
         4) en passant target
         5) halfmove clock
         6) fullmove number

        Then recompute zobrist_hash and reset history.
        """
        parts = fen.split()
        # 1) Piece placement
        rows = parts[0].split("/")
        self.squares = [[self.EMPTY] * 8 for _ in range(8)]
        for rank_idx, row in enumerate(rows):
            file = 1
            for ch in row:
                if ch.isdigit():
                    file += int(ch)
                else:
                    rank = 8 - rank_idx
                    self[(file, rank)] = ch
                    file += 1

        # 2) Side to move
        self.side_to_move = "white" if parts[1] == "w" else "black"

        # 3) Castling rights
        castle = parts[2]
        self.white_can_castle_kingside = "K" in castle
        self.white_can_castle_queenside = "Q" in castle
        self.black_can_castle_kingside = "k" in castle
        self.black_can_castle_queenside = "q" in castle

        # 4) En passant
        ep = parts[3]
        if ep != "-":
            file = "abcdefgh".index(ep[0]) + 1
            rank = int(ep[1])
            self.en_passant_target = (file, rank)
        else:
            self.en_passant_target = None

        # 5) & 6) Clocks
        self.halfmove_clock = int(parts[4])
        self.fullmove_number = int(parts[5])

        # Recompute Zobrist & history
        self.zobrist_hash = self.zobrist.compute_hash(self, self.side_to_move)
        self.history = [self.zobrist_hash]

    # ──────────────────────────────────────────────────────────────
    # Incremental Zobrist helpers – now aligned with Zobrist API
    # ──────────────────────────────────────────────────────────────

    def xor_piece_hash(self, piece: str, sq: Tuple[int, int]):
        """XOR the hash for *piece* located on *sq* (file, rank)."""
        if piece == self.EMPTY:
            return
        p_idx = self.zobrist.piece_index(piece)
        s_idx = self.zobrist.square_index(*sq)
        self.zobrist_hash ^= self.zobrist.piece_square[p_idx][s_idx]

    def xor_castling_rights(self, rights: Tuple[bool, bool, bool, bool]):
        """XOR whichever castling‑right bits are *True* in *rights*."""
        for flag, key in zip(rights, ("WK", "WQ", "BK", "BQ")):
            if flag:
                self.zobrist_hash ^= self.zobrist.castling_rights[key]

    def xor_en_passant(self, ep: Optional[Tuple[int, int]]):
        if ep is None:
            return
        file, rank = ep
        # Zobrist uses the *file* only, but we sanity‑check rank
        # to mimic `compute_hash`.
        if rank in (3, 6):
            self.zobrist_hash ^= self.zobrist.en_passant[file]

    # ──────────────────────────────────────────────────────────────
    # Board‑wide helpers
    # ──────────────────────────────────────────────────────────────

    def _update_castling_from_board(self) -> None:
        """Disable any castling right whose rook has vanished."""
        self.white_can_castle_queenside &= self[(1, 1)] == "R"
        self.white_can_castle_kingside &= self[(8, 1)] == "R"
        self.black_can_castle_queenside &= self[(1, 8)] == "r"
        self.black_can_castle_kingside &= self[(8, 8)] == "r"

    # ------------------------------------------------------------------
    # Move application
    # ------------------------------------------------------------------

    def make_move(
        self, move: "Move"
    ) -> Tuple[Tuple[bool, bool, bool, bool], int]:
        """Execute *``move``* on the board, updating all incremental data
        structures (clocks, Zobrist hash, castling rights…).  Returns a tuple
        containing the **previous** castling-rights bit-set and the previous
        half-move clock so that :py:meth:`undo_move` can restore them.
        """
        reset_clock = False
        from_sq = move.from_sq
        to_sq = move.to_sq
        promo = move.promo

        # snapshot state that `undo_move` will need
        prev_rights = (
            self.white_can_castle_kingside,
            self.white_can_castle_queenside,
            self.black_can_castle_kingside,
            self.black_can_castle_queenside,
        )
        prev_halfmove = self.halfmove_clock
        prev_en_passant = self.en_passant_target
        move.prev_en_passant = prev_en_passant
        prev_side_to_move = self.side_to_move

        # ──────────────────────────────────────────────────────────
        # Zobrist – remove «side to move»
        # ──────────────────────────────────────────────────────────
        self.zobrist_hash ^= self.zobrist.side_to_move

        # ──────────────────────────────────────────────────────────
        # Zobrist – remove *old* castling/en‑passant info
        # ──────────────────────────────────────────────────────────
        self.xor_castling_rights(prev_rights)
        self.xor_en_passant(prev_en_passant)

        # ──────────────────────────────────────────────────────────
        # Zobrist – remove moving piece from its origin square
        # ──────────────────────────────────────────────────────────
        piece = self[from_sq]
        self.xor_piece_hash(piece, from_sq)

        # ──────────────────────────────────────────────────────────
        # Captures (including en‑passant)
        # ──────────────────────────────────────────────────────────
        if self.en_passant_target and to_sq == self.en_passant_target:
            # en‑passant capture
            move.is_en_passant = True
            direction = 1 if piece.isupper() else -1
            cap_sq = (to_sq[0], to_sq[1] - direction)
            move.captured = (self[cap_sq], cap_sq)
            self.xor_piece_hash(self[cap_sq], cap_sq)
            self[cap_sq] = self.EMPTY
            reset_clock = True
        else:
            captured_piece = self[to_sq]
            if captured_piece != Board.EMPTY:
                move.captured = (captured_piece, to_sq)
                self.xor_piece_hash(captured_piece, to_sq)
                reset_clock = True

        # ──────────────────────────────────────────────────────────
        # Castling – move the rook first so that hash updates are clear
        # ──────────────────────────────────────────────────────────
        if piece.upper() == "K" and abs(to_sq[0] - from_sq[0]) == 2:
            move.is_castle = True
            rank = from_sq[1]
            if to_sq[0] > from_sq[0]:  # kingside
                rook_from = (8, rank)
                rook_to = (6, rank)
            else:  # queenside
                rook_from = (1, rank)
                rook_to = (4, rank)

            rook_piece = self[rook_from]
            # XOR out rook at its origin, move it, XOR in at destination
            self.xor_piece_hash(rook_piece, rook_from)
            self[rook_from] = self.EMPTY
            self[rook_to] = rook_piece
            self.xor_piece_hash(rook_piece, rook_to)

        # ──────────────────────────────────────────────────────────
        # Promotion / normal piece placement
        # ──────────────────────────────────────────────────────────
        if promo:
            assert piece.upper() == "P", "Promotion only applies to pawns"
            placed_piece = promo if piece.isupper() else promo.lower()
        else:
            placed_piece = piece

        self[to_sq] = placed_piece
        self[from_sq] = Board.EMPTY

        # XOR in placed piece on its destination square
        self.xor_piece_hash(placed_piece, to_sq)

        # ──────────────────────────────────────────────────────────
        # Update en‑passant target & castling rights flags
        # ──────────────────────────────────────────────────────────
        if piece.upper() == "P" and abs(to_sq[1] - from_sq[1]) == 2:
            self.en_passant_target = (from_sq[0], (from_sq[1] + to_sq[1]) // 2)
        else:
            self.en_passant_target = None

        # explicit flag updates
        if piece == "K":
            self.white_can_castle_kingside = False
            self.white_can_castle_queenside = False
        elif piece == "k":
            self.black_can_castle_kingside = False
            self.black_can_castle_queenside = False
        elif piece == "R":
            if from_sq == (1, 1) or to_sq == (1, 1):
                self.white_can_castle_queenside = False
            if from_sq == (8, 1) or to_sq == (8, 1):
                self.white_can_castle_kingside = False
        elif piece == "r":
            if from_sq == (1, 8) or to_sq == (1, 8):
                self.black_can_castle_queenside = False
            if from_sq == (8, 8) or to_sq == (8, 8):
                self.black_can_castle_kingside = False

        # also disable any rights for which the rook
        # has vanished due to capture
        self._update_castling_from_board()

        # ──────────────────────────────────────────────────────────
        # Zobrist – add new castling & en‑passant info
        # ──────────────────────────────────────────────────────────
        new_rights = (
            self.white_can_castle_kingside,
            self.white_can_castle_queenside,
            self.black_can_castle_kingside,
            self.black_can_castle_queenside,
        )
        self.xor_castling_rights(new_rights)
        self.xor_en_passant(self.en_passant_target)

        # ──────────────────────────────────────────────────────────
        # Zobrist – add «side to move» for the *next* player
        # ──────────────────────────────────────────────────────────
        self.side_to_move = (
            "black" if prev_side_to_move == "white" else "white"
        )
        self.zobrist_hash ^= self.zobrist.side_to_move

        # ──────────────────────────────────────────────────────────
        # Clocks
        # ──────────────────────────────────────────────────────────
        if piece.upper() == "P" or reset_clock:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if piece.islower():  # Black just moved → increment fullmove counter
            self.fullmove_number += 1

        self.history.append(self.zobrist_hash)

        return prev_rights, prev_halfmove

    # ------------------------------------------------------------------
    # Move rollback
    # ------------------------------------------------------------------

    # ───────── Undo last move ─────────
    def undo_move(
        self,
        move: "Move",
        prev_rights: tuple[bool, bool, bool, bool],
        prev_halfmove_clock: int,
    ) -> None:

        from_sq, to_sq = move.from_sq, move.to_sq
        self.history.pop()

        # hash-out *current* side-to-move (the one that just played)
        self.zobrist_hash ^= self.zobrist.side_to_move

        # hash-out current rights & en-passant before they change back
        cur_rights = (
            self.white_can_castle_kingside,
            self.white_can_castle_queenside,
            self.black_can_castle_kingside,
            self.black_can_castle_queenside,
        )
        self.xor_castling_rights(cur_rights)
        self.xor_en_passant(self.en_passant_target)

        # hash-out the piece that sits on `to_sq`
        # (it’s about to move back)
        moving_piece = self[to_sq]
        self.xor_piece_hash(moving_piece, to_sq)

        # ─── promotion rollback ───
        if move.promo:
            moving_piece = "P" if moving_piece.isupper() else "p"

        # move the piece back & hash-in on `from_sq`
        self[from_sq] = moving_piece
        self.xor_piece_hash(moving_piece, from_sq)
        self[to_sq] = self.EMPTY

        # restore captured pawn / piece (incl. en-passant)
        if move.captured:
            cap_piece, cap_sq = move.captured
            self[cap_sq] = cap_piece
            self.xor_piece_hash(cap_piece, cap_sq)

        # undo rook shift if the move was castling
        if move.is_castle:
            rank = from_sq[1]
            rook_from, rook_to = (
                ((8, rank), (6, rank))
                if to_sq[0] > from_sq[0]  # kingside
                else ((1, rank), (4, rank))  # queenside
            )
            self.xor_piece_hash(
                self[rook_to], rook_to
            )  # hash-out rook on f/d-file
            self[rook_from] = self[rook_to]  # move rook back
            self.xor_piece_hash(
                self[rook_from], rook_from
            )  # hash-in rook on h/a-file
            self[rook_to] = self.EMPTY

        # restore clocks, rights, en-passant
        self.halfmove_clock = prev_halfmove_clock
        self.en_passant_target = move.prev_en_passant

        (
            self.white_can_castle_kingside,
            self.white_can_castle_queenside,
            self.black_can_castle_kingside,
            self.black_can_castle_queenside,
        ) = prev_rights

        # hash-in restored rights & en-passant
        self.xor_castling_rights(prev_rights)
        self.xor_en_passant(self.en_passant_target)

        # flip side-to-move back and hash-in
        self.side_to_move = (
            "black" if self.side_to_move == "white" else "white"
        )
        self.zobrist_hash ^= self.zobrist.side_to_move

        # full-move number rolls back only when
        # we’re rewinding Black’s move
        if self.side_to_move == "black" and self.fullmove_number > 1:
            self.fullmove_number -= 1
