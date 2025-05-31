from typing import List
from engine.bitboard.move import Move
from engine.bitboard.utils import pop_lsb
from engine.bitboard.constants import ROOK_OFFSETS


def generate_rook_moves(
    rook_bb: int, my_occ: int, their_occ: int
) -> List[Move]:
    """
    Generate all legal rook moves
    (including captures) for the given bitboard.
    """
    moves: List[Move] = []

    tmp_rooks = rook_bb
    while tmp_rooks:
        src = pop_lsb(tmp_rooks)

        # For each orthogonal direction
        for offset in ROOK_OFFSETS:
            # Determine file shift per step:
            #   +1 for north moves, -1 for south
            file_delta = offset
            if offset == 8 or offset == -8:
                file_delta = 0

            cur = src
            while True:
                prev_file = cur & 7
                # break if horizontal wrap
                if (file_delta == 1 and prev_file == 7) or (
                    file_delta == -1 and prev_file == 0
                ):
                    break

                tgt = cur + offset
                # break if off-board
                if tgt < 0 or tgt >= 64:
                    break

                # 1) Blocked by own piece?
                if my_occ & (1 << tgt):
                    break

                # 2) Enemy capture?
                if their_occ & (1 << tgt):
                    moves.append(Move(src, tgt, capture=True))
                    break

                # 3) Quiet move
                moves.append(Move(src, tgt))

                # advance
                cur = tgt

        tmp_rooks &= tmp_rooks - 1
    return moves
