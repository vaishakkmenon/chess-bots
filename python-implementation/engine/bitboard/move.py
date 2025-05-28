# engine/bitboard/move.py
__all__ = ["Move"]


class Move:
    def __init__(self, src: int, dst: int):
        self.src = src
        self.dst = dst

    def __repr__(self):
        return f"Move({self.src}->{self.dst})"

    def __eq__(self, other):
        return (
            isinstance(other, Move)
            and self.src == other.src
            and self.dst == other.dst
        )
