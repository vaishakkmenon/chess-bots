from typing import Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from engine.bitboard.move import Move


class Undo:
    def __init__(
        self,
        move: Move,
        old_ep: int,
        captured_idx: Optional[int],
        cap_sq: Optional[int],
        prev_side: int,
        old_castling_rights: int,
    ) -> None:
        self.move: Move = move
        self.old_ep: int = old_ep
        self.captured_idx: Optional[int] = captured_idx
        self.cap_sq: Optional[int] = cap_sq
        self.prev_side: int = prev_side
        self.old_castling_rights: int = old_castling_rights
