from typing import Optional


def pop_lsb(bb: int) -> Optional[int]:
    """
    Remove and return the index (0-63) of the least-significant 1-bit in bb.
    Return None if bb == 0.
    """
    if bb == 0:
        return None
    lsb_bb = bb & -bb
    idx = lsb_bb.bit_length() - 1
    return idx


def bit_count(bb: int) -> int:
    """
    Return the number of 1-bits in bb.
    """
    return bb.bit_count()


def lsb(bb: int) -> Optional[int]:
    """
    Return index of least-significant 1-bit without clearing it.
    Return None if bb == 0.
    """
    if bb == 0:
        return None
    return (bb & -bb).bit_length() - 1


def msb(bb: int) -> Optional[int]:
    """
    Return index of most-significant 1-bit without clearing it.
    Return None if bb == 0.
    """
    if bb == 0:
        return None
    return bb.bit_length() - 1


def print_bitboard(bb: int, source_sq: Optional[int] = None) -> None:
    """
    Print an 8x8 ASCII board for the given bitboard mask.
    Marks the source_sq with 'S' (if provided),
    attack squares with 'X', and empty with '.'.
    Rows labeled 8→1 and files a→h.
    """
    print()
    # Print ranks 8 down to 1
    for rank in range(8, 0, -1):
        row = [str(rank)]
        for file in range(8):
            sq = (rank - 1) * 8 + file
            if source_sq is not None and sq == source_sq:
                row.append("S")
            elif (bb >> sq) & 1:
                row.append("X")
            else:
                row.append(".")
        print(" ".join(row))
    # File labels
    print("  " + " ".join(chr(ord("a") + f) for f in range(8)))
