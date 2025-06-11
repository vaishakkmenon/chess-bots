# engine/bitboard/config.py
from typing import Tuple, Optional

# When True, all move‐generation returns "raw tuples" instead of Move objects
USE_RAW_MOVES = False

# A RawMove is exactly (src, dst, capture, promotion, en_passant, castling)
RawMove = Tuple[int, int, bool, Optional[str], bool, bool]
RawHistoryEntry = Tuple[
    int,  # piece_idx
    int,  # src square index
    int,  # dst square index
    Optional[int],  # captured_idx (None if no capture)
    Optional[int],  # cap_sq (square of captured piece if any)
    Optional[int],  # old_ep square index (None if none)
    int,  # prev_side (WHITE or BLACK)
    int,  # old_castling rights bitmask
    Optional[str],  # promotion character (None if no promotion)
    bool,  # en_passant flag
    bool,  # castling flag
    int,  # halfmove_clock after move
    int,  # fullmove_number after move
]
