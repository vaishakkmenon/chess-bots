from typing import Dict
from engine.bitboard.board import Board  # noqa:TC002
from engine.bitboard.config import RawMove  # noqa: TC002
from engine.bitboard.generator import generate_legal_moves


def perft_count(board: Board, depth: int) -> int:
    """
    A “count-only” perft that returns the total leaf
    nodes at exactly `depth` plies beneath `board`.
    Faster than building a dict at every node.
    """
    # Bind hot attributes to locals to avoid repeated lookups
    gen_moves = generate_legal_moves
    make_move = board.make_move_raw
    undo_move = board.undo_move_raw

    def _dfs(d: int) -> int:
        if d == 0:
            return 1

        total = 0
        for move in gen_moves(board):
            make_move(move)
            total += _dfs(d - 1)
            undo_move()
        return total

    return _dfs(depth)


# TESTING FUNCTION ONLY
def perft_divide(board: Board, depth: int) -> Dict[RawMove, int]:
    if depth == 0:
        return {}

    results = {}
    for move in generate_legal_moves(board):
        board.make_move_raw(move)
        results[move] = perft_count(board, depth - 1)
        board.undo_move_raw()
    return results


def perft_hashed(
    board: Board, depth: int, table: Dict[tuple[int, int], int]
) -> int:
    """
    A transposition-table-enabled perft:
    table[(zobrist_hash, depth)] = node count
    """
    key = (board.zobrist_hash, depth)
    if key in table:
        return table[key]

    if depth == 0:
        return 1

    total = 0
    for move in generate_legal_moves(board, board.side_to_move):
        board.make_move_raw(move)
        total += perft_hashed(board, depth - 1, table)
        board.undo_move_raw()

    table[key] = total
    return total
