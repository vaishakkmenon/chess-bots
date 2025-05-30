# engine/bitboard/move.py
__all__ = ["Move"]


class Move:
    def __init__(
        self,
        src: int,
        dst: int,
        capture: bool = False,
        promotion: str | None = None,
        en_passant: bool = False,
    ):
        self.src = src
        self.dst = dst
        self.capture = capture
        self.promotion = promotion
        self.en_passant = en_passant

    def __repr__(self):
        promo = f"={self.promotion}" if self.promotion else ""
        cap = "x" if self.capture else ""
        ep = " e.p." if self.en_passant else ""
        return f"Move({self.src}{cap}->{self.dst}{promo}{ep})"

    def __eq__(self, other):
        return (
            isinstance(other, Move)
            and self.src == other.src
            and self.dst == other.dst
            and self.capture == other.capture
            and self.promotion == other.promotion
            and self.en_passant == other.en_passant
        )
