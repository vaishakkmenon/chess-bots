# engine/bitboard/config.py
from typing import Tuple, Optional

# When True, all move‐generation returns "raw tuples" instead of Move objects
USE_RAW_MOVES = False

# A RawMove is exactly (src, dst, capture, promotion, en_passant, castling)
RawMove = Tuple[int, int, bool, Optional[str], bool, bool]
