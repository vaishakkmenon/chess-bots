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
