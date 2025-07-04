from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from engine.bitboard.move import Move

if TYPE_CHECKING:
    from engine.bitboard.config import RawMove

# from engine.bitboard.config import RawMove


def algebraic_to_index(coord: str) -> int:
    """
    Convert algebraic coordinates (e.g. "a1", "e4", "h8")
    into a 0-63 square index, where:
      a1 → 0, b1 → 1, …, h1 → 7,
      a2 → 8, …, h8 → 63.
    """
    file_char = coord[0].lower()
    rank_char = coord[1]
    file = ord(file_char) - ord("a")
    rank = int(rank_char) - 1
    if not (0 <= file < 8 and 0 <= rank < 8):
        raise ValueError(f"Invalid square: {coord}")
    return rank * 8 + file


def index_to_algebraic(sq: int) -> str:
    """
    0 -> 'a1', 1 -> 'b1', ..., 63 -> 'h8'
    """
    file = sq % 8
    rank = sq // 8
    return f"{chr(ord('a')+file)}{rank+1}"


def tuple_to_move(raw: RawMove) -> Move:
    src, dst, capture, promotion, en_passant, castling = raw
    return Move(
        src,
        dst,
        capture=capture,
        promotion=promotion,
        en_passant=en_passant,
        castling=castling,
    )


def move_to_tuple(move: Move) -> RawMove:
    return (
        move.src,
        move.dst,
        move.capture,
        move.promotion,
        move.en_passant,
        move.castling,
    )


def expand_occupancy(subset_index: int, relevant_mask: int) -> int:
    """
    Given a relevant_mask (bitboard) of N squares,
    and a subset_index in [0..2^N-1], return a bitboard (64-bit int)
    whose bits are a subset of relevant_mask: the k-th 1-bit of
    relevant_mask is set in the result if and only if the
    k-th bit of subset_index is 1.
    """
    positions: List[int] = []
    temp = relevant_mask
    while temp:
        bit_sq = pop_lsb(temp)
        assert bit_sq is not None
        positions.append(bit_sq)
        temp &= temp - 1

    occ = 0
    for k in range(len(positions)):
        if (subset_index >> k) & 1:
            occ |= 1 << positions[k]
    return occ


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
