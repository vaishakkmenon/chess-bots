from typing import Dict
from engine.bitboard.board import Board  # noqa:TC002
from engine.bitboard.config import RawMove  # noqa: TC002
from engine.bitboard.generator import generate_legal_moves

from engine.bitboard.status import (
    is_fifty_move_draw,
    is_fivefold_repetition,
    is_insufficient_material,
    is_threefold_repetition,
)


from collections import Counter

lookups_by_depth: Counter[int] = Counter()
hits_by_depth: Counter[int] = Counter()


def perft_count(
    board: Board,
    depth: int,
    *,
    respect_draws: bool = False,
) -> int:
    """
    A “count-only” perft that returns the total leaf
    nodes at exactly `depth` plies beneath `board`.
    Faster than building a dict at every node.
    If ``respect_draws`` is True, recursion stops early when a
    draw by the fifty-move rule, repetition, or insufficient
    material is detected.
    """
    # Bind hot attributes to locals to avoid repeated lookups
    gen_moves = generate_legal_moves
    make_move = board.make_move_raw
    undo_move = board.undo_move_raw

    def _dfs(d: int) -> int:
        if d == 0:
            return 1

        if respect_draws and (
            is_fifty_move_draw(board)
            or is_threefold_repetition(board)
            or is_fivefold_repetition(board)
            or is_insufficient_material(board)
        ):
            return 1

        total = 0
        for move in gen_moves(board):
            make_move(move)
            total += _dfs(d - 1)
            undo_move()
        return total

    return _dfs(depth)


# TESTING FUNCTION ONLY
def perft_divide(
    board: Board, depth: int, *, respect_draws: bool = False
) -> Dict[RawMove, int]:
    if depth == 0:
        return {}

    results: Dict[RawMove, int] = {}
    for move in generate_legal_moves(board):
        board.make_move_raw(move)
        results[move] = perft_count(
            board,
            depth - 1,
            respect_draws=respect_draws,
        )
        board.undo_move_raw()
    return results


def perft_hashed(
    board: Board,
    depth: int,
    table: Dict[tuple[int, int], int],
    cur_depth: int,
    *,
    respect_draws: bool = False,
) -> int:
    if depth == 0:
        return 1

    key = (board.zobrist_key, depth)
    lookups_by_depth[cur_depth] += 1
    if key in table:
        hits_by_depth[cur_depth] += 1
        return table[key]

    total = 0
    for move in generate_legal_moves(board):
        board.make_move_raw(move)
        total += perft_hashed(
            board,
            depth - 1,
            table,
            cur_depth + 1,
            respect_draws=respect_draws,
        )
        board.undo_move_raw()

    table[key] = total
    return total


def perft_hashed_root(board: Board, depth: int) -> int:
    lookups_by_depth.clear()
    hits_by_depth.clear()
    table: Dict[tuple[int, int], int] = {}
    total = perft_hashed(board, depth, table, cur_depth=0)

    print("\nTransposition Table Stats:")
    for d in sorted(lookups_by_depth):
        looks = lookups_by_depth[d]
        hits = hits_by_depth[d]
        print(
            f" depth={d:2d}  lookups={looks:7d}  hits={hits:7d}  hit-rate={hits/looks:.1%}"  # noqa: E501
        )

    return total
