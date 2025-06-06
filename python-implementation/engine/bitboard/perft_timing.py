import time
from collections import defaultdict
from engine.bitboard.board import Board

# from engine.bitboard.config import RawMove

from engine.bitboard.generator import generate_legal_moves

# ——————————————————————————————————————————————————————————————————————————————
# ASSUMPTIONS:
#   1. You have a function `generate_legal_moves(board)`
#      that returns a Python list of Move‐objects
#      (and it internally calls `in_check` on each pseudo‐legal move).
#   2. Your Board class has methods:
#        board.make_move(move)
#        board.undo_move()
#      which exactly revert one move.
#   3. You want to profile a full perft from
#      depth 1 up to depth max_depth in one go.
#
# USAGE:
#   1. Call `run_perft_profile_with_progress(initial_board, max_depth)` once.
#   2. The code will recurse down to `max_depth`, collecting per‐depth timings.
#   3. When it’s done, it will print a table to
#      stdout and append the same table to
#      “perft_profile.log” in the current directory.
# ——————————————————————————————————————————————————————————————————————————————

# --- Global accumulators (reset before each full perft run) ---
gen_time = defaultdict(
    float
)  # gen_time[d] = total time spent in generate at depth d
move_time = defaultdict(
    float
)  # move_time[d] = total time in make/recursion/undo at depth d
positions_count = defaultdict(
    int
)  # positions_count[d] = number of nodes visited at depth d


def perft_profile(board, depth, cur_depth):
    """
    Recursively walks the tree, accumulating per‐depth:
      - positions_count[cur_depth]
      - gen_time[cur_depth]   (time spent in generate_legal_moves at that depth)
      - move_time[cur_depth]  (time spent in make_move + recursion + undo at that depth)

    Returns the leaf‐node count for this subtree.
    """  # noqa: E501
    # Count this position at cur_depth
    positions_count[cur_depth] += 1

    if depth == 0:
        return 1

    # 1) Time the generation of legal moves at this depth
    t0 = time.perf_counter()
    moves = generate_legal_moves(board)
    gen_time[cur_depth] += time.perf_counter() - t0

    nodes = 0
    # 2) Time each make + recursive call + undo
    for move in moves:
        t1 = time.perf_counter()
        board.make_move_raw(move)
        nodes += perft_profile(board, depth - 1, cur_depth + 1)
        board.undo_move_raw()
        move_time[cur_depth] += time.perf_counter() - t1

    return nodes


def run_perft_profile_with_progress(root_board, max_depth):
    """
    1) Clears accumulators (including raw_history).
    2) Generates all legal moves at root (depth = 1). Times that call → gen_time[1].
    3) For each top‐move, use make_move_raw or make_move depending on config.USE_RAW_MOVES,
       recurse into perft_profile, then undo with undo_move_raw or undo_move.
    4) Print + log a per‐depth timing table when done.
    """  # noqa: E501
    # --- 1) Reset accumulators ---
    gen_time.clear()
    move_time.clear()
    positions_count.clear()
    root_board.raw_history.clear()  # clear any leftover raw history

    # --- 2) Root‐level generate (depth = 1) ---
    positions_count[1] = 1  # count the root itself
    t0_root = time.perf_counter()
    top_moves = generate_legal_moves(root_board)
    gen_time[1] += time.perf_counter() - t0_root

    total_top = len(top_moves)
    total_nodes = 0

    # --- 3) Iterate top‐moves with raw vs. object branching ---
    for idx, move in enumerate(top_moves, start=1):
        print(f">> Processing top‐move {idx}/{total_top} …", end="\n")
        t1 = time.perf_counter()
        root_board.make_move_raw(move)
        nodes_from_subtree = perft_profile(root_board, max_depth - 1, 2)
        root_board.undo_move_raw()
        move_time[1] += time.perf_counter() - t1
        total_nodes += nodes_from_subtree

    # Clear the progress line
    print(f"✔ Completed all {total_top} top‐moves.{' ' * 20}")

    # --- 4) Print + log per‐depth breakdown ---
    with open("perft_profile.log", "a") as logfile:
        header = (
            f"\nPerft Profile (max_depth = {max_depth})\n"
            "Depth │ Positions │   Gen Time (s)   │  Move+Recurse Time (s)  │ Total Time (s)\n"  # noqa: E501
            "──────┼───────────┼──────────────────┼─────────────────────────┼───────────────\n"  # noqa: E501
        )
        print(header, end="")
        logfile.write(header)

        for d in range(1, max_depth + 1):
            pos = positions_count.get(d, 0)
            gt = gen_time.get(d, 0.0)
            mt = move_time.get(d, 0.0)
            tot_t = gt + mt

            line = f"{d:>5} │ {pos:>9,} │ {gt:>16.6f} │ {mt:>23.6f} │ {tot_t:>13.6f}\n"  # noqa: E501
            print(line, end="")
            logfile.write(line)

        footer = (
            f"\nTotal leaf‐node count at depth {max_depth}: {total_nodes:,}\n"
        )
        print(footer)
        logfile.write(footer)

    return total_nodes


# ——————————————————————————————————————————————————————————————————————————————
# Example invocation:
#
if __name__ == "__main__":
    initial = Board()  # however you create a fresh start position
    run_perft_profile_with_progress(initial, 6)
