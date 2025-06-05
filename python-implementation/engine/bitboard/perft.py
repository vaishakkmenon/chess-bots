from typing import Dict
from engine.bitboard.move import Move  # noqa:TC002
from engine.bitboard.board import Board  # noqa:TC002
from engine.bitboard.generator import generate_legal_moves


def perft_count(board: Board, depth: int) -> int:
    """
    A “count-only” perft that returns the total leaf
    nodes at exactly `depth` plies beneath `board`.
    Faster than building a dict at every node.
    """
    # Bind hot attributes to locals to avoid repeated lookups
    gen_moves = generate_legal_moves
    mk_move = board.make_move
    un_move = board.undo_move

    def _dfs(d: int) -> int:
        if d == 0:
            return 1

        total = 0
        for mv in gen_moves(board):
            mk_move(mv)
            total += _dfs(d - 1)
            un_move()
        return total

    return _dfs(depth)


# TESTING FUNCTION ONLY
def perft_divide(board: Board, depth: int) -> Dict[Move, int]:
    if depth == 0:
        return 1

    results = {}
    for move in generate_legal_moves(board):
        board.make_move(move)
        results[move] = perft_count(board, depth - 1)
        board.undo_move()
    return results
