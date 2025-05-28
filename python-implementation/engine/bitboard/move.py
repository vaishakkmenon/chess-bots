# engine/bitboard/move.py
__all__ = ["Move"]


class Move:
    def __init__(
        self,
        src: int,
        dst: int,
        capture: bool = False,
        promotion: str | None = None,
    ):
        self.src = src
        self.dst = dst
        self.capture = capture
        self.promotion = promotion

    def __repr__(self):
        promo = f"={self.promotion}" if self.promotion else ""
        cap = "x" if self.capture else ""
        return f"Move({self.src}{cap}->{self.dst}{promo})"

    def __eq__(self, other):
        return (
            isinstance(other, Move)
            and self.src == other.src
            and self.dst == other.dst
            and self.capture == other.capture
            and self.promotion == other.promotion
        )
