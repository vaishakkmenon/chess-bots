from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Move:
    # The square the piece is moving from, as (file, rank) — e.g. (5, 2) for e2
    from_sq: Tuple[int, int]

    # The square the piece is moving to, as (file, rank) — e.g. (5, 4) for e4
    to_sq: Tuple[int, int]

    # Promotion piece character ("Q", "R", "B", or "N")
    # if this is a promotion move; otherwise None
    promo: Optional[str] = None

    # True if this move is a castling move (king moves two squares)
    is_castle: bool = False

    # True if this move is an en passant capture
    is_en_passant: bool = False

    # En-passant capture square
    prev_en_passant: Optional[Tuple[int, int]] = None

    # The piece that was captured on this move, if any (used for undo and eval)
    captured: Optional[Tuple[str, Tuple[int, int]]] = None
