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
        castling: bool = False,
    ):
        self.src = src
        self.dst = dst
        self.capture = capture
        self.promotion = promotion
        self.en_passant = en_passant
        self.castling = castling

    def __repr__(self):
        promo = f"={self.promotion}" if self.promotion else ""
        cap = "x" if self.capture else ""
        ep = " e.p." if self.en_passant else ""
        cas = "cas" if self.castling else ""
        return f"Move({self.src}{cap}->{self.dst}{promo}{ep}{cas})"

    def __eq__(self, other: object):
        return (
            isinstance(other, Move)
            and self.src == other.src
            and self.dst == other.dst
            and self.capture == other.capture
            and self.promotion == other.promotion
            and self.en_passant == other.en_passant
            and self.castling == other.castling
        )

    def __hash__(self) -> int:  # noqa: D401 - trivial hashing
        """Return a hash based on move attributes."""
        return hash(
            (
                self.src,
                self.dst,
                self.capture,
                self.promotion,
                self.en_passant,
                self.castling,
            )
        )
