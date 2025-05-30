from typing import List
from engine.bitboard.move import Move
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import BISHOP_OFFSETS


def generate_bishop_moves(
    bishops_bb: int, my_occ: int, their_occ: int
) -> List[Move]:
    """
    Generate all legal bishop moves
    (including captures) for the given bitboard.
    """
    moves: List[Move] = []

    tmp_bishops = bishops_bb
    while tmp_bishops:
        src = pop_lsb(tmp_bishops)

        # For each diagonal direction
        for offset in BISHOP_OFFSETS:
            # Determine file shift per step:
            #   +1 for east moves, -1 for west
            file_delta = 1 if offset in (9, -7) else -1

            cur = src
            while True:
                prev_file = cur & 7
                if (prev_file == 7 and file_delta == 1) or (
                    prev_file == 0 and file_delta == -1
                ):
                    break

                tgt = cur + offset
                if tgt < 0 or tgt >= 64:
                    break

                # 1) Blocked by our own piece?
                if my_occ & (1 << tgt):
                    break

                # 2) Enemy capture?
                if their_occ & (1 << tgt):
                    moves.append(Move(src, tgt, capture=True))
                    break

                # 3) Quiet move
                moves.append(Move(src, tgt))

                # advance to next square
                cur = tgt

        tmp_bishops &= tmp_bishops - 1
    return moves
