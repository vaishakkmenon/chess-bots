from typing import Dict
from engine.board import Board  # noqa: TC002
from engine.moves.generator import legal_moves


def perft(board: Board, depth: int) -> int:
    """
    Count leaf nodes reachable in `depth` plies from `board`.
    """
    if depth < 0:
        raise ValueError(f"perft: negative depth {depth}")
    if depth == 0:
        return 1

    total = 0
    all_moves = legal_moves(board, board.side_to_move)
    for move in all_moves:
        previous_move = board.make_move(move)
        count = perft(board, depth - 1)
        board.undo_move(move, *previous_move)
        total += count
    return total


def perft_divide(board: Board, depth: int) -> Dict[str, int]:
    """
    Return a map UCI-string → perft count at depth-1 under that move.
    """
    if depth < 1:
        return {}

    results: Dict[str, int] = {}
    all_moves = legal_moves(board, board.side_to_move)
    for move in all_moves:
        key = board.uci(move)
        previous_move = board.make_move(move)
        results[key] = perft(board, depth - 1)
        board.undo_move(move, *previous_move)
    return results


def perft_hashed(
    board: Board, depth: int, table: dict[tuple[int, int], int]
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
    for mv in legal_moves(board, board.side_to_move):
        prev = board.make_move(mv)
        total += perft_hashed(board, depth - 1, table)
        board.undo_move(mv, *prev)

    table[key] = total
    return total
