import re

# import time
import pytest

from engine.mailbox.board import Board
from engine.mailbox.zobrist import Zobrist
from engine.mailbox.moves.generator import legal_moves
from engine.mailbox.perft import perft, perft_divide, perft_hashed

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

UCI_PATTERN = re.compile(r"^[a-h][1-8][a-h][1-8]$")


def make_start_board() -> Board:
    b = Board(Zobrist())
    b.init_positions()
    return b


def make_kiwipete_board() -> Board:
    b = Board(Zobrist())
    b.set_fen(
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    )
    return b


# ──────────────────────────────────────────────────────────────────────────────
# Perft correctness tests
# ──────────────────────────────────────────────────────────────────────────────


def test_perft_depth_zero_is_one():
    b = make_start_board()
    assert perft(b, 0) == 1


def test_perft_depth_one_equals_legal_moves():
    b = make_start_board()
    moves = legal_moves(b, b.side_to_move)
    assert perft(b, 1) == len(moves)


@pytest.mark.parametrize(
    "depth,expected",
    [
        (1, 20),
        (2, 400),
        (3, 8902),
    ],
)
def test_perft_starting_position(depth, expected):
    b = make_start_board()
    assert perft(b, depth) == expected


# ──────────────────────────────────────────────────────────────────────────────
# Perft Divide tests
# ──────────────────────────────────────────────────────────────────────────────


def test_perft_divide_depth_one_sums_to_perft():
    b = make_start_board()
    total = perft(b, 1)
    divide = perft_divide(b, 1)

    # 1) Sum matches perft
    assert sum(divide.values()) == total

    # 2) Keys are UCI-legal
    for mv_str in divide.keys():
        assert UCI_PATTERN.match(mv_str), f"Invalid UCI move key: {mv_str}"

    # 3) Each result is 1 at depth 1
    assert all(cnt == 1 for cnt in divide.values())

    # 4) Keys are unique
    assert len(divide) == len(set(divide))


def test_perft_divide_consistency_with_depth_two():
    b = make_start_board()
    total2 = perft(b, 2)
    divide2 = perft_divide(b, 2)

    assert sum(divide2.values()) == total2
    assert any(cnt > 1 for cnt in divide2.values())


def test_divide_keys_are_legal_moves():
    b = make_start_board()
    divide = perft_divide(b, 1)
    legal_uci = {
        f"{chr(m.from_sq[0]+96)}{m.from_sq[1]}{chr(m.to_sq[0]+96)}{m.to_sq[1]}"
        for m in legal_moves(b, b.side_to_move)
    }
    assert set(divide.keys()).issubset(legal_uci)


def test_perft_rejects_negative_depth():
    b = make_start_board()
    with pytest.raises(ValueError):
        perft(b, -1)


# ──────────────────────────────────────────────────────────────────────────────
# Kiwipete known values
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "depth,expected",
    [
        (1, 48),
        (2, 2039),
        (3, 97862),
    ],
)
def test_perft_kiwipete(depth, expected):
    b = make_kiwipete_board()
    assert perft(b, depth) == expected


# ──────────────────────────────────────────────────────────────────────────────
# Correctness
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("depth", [1, 2, 3])
def test_perft_hashed_matches_naive(depth):
    b1 = make_start_board()
    naive = perft(b1, depth)

    b2 = make_start_board()
    table = {}
    hashed = perft_hashed(b2, depth, table)

    assert (
        hashed == naive
    ), f"perft_hashed({depth})={hashed} should match perft({depth})={naive}"


# ──────────────────────────────────────────────────────────────────────────────
# Performance comparison
# ──────────────────────────────────────────────────────────────────────────────

# Commenting comparison function because it takes a while
# def test_perft_hashed_performance():
#     """
#     Compare timings on a modest perft (depth=5).
#     This prints out both runtimes
#     so you can see the speedup from using a transposition table.
#     """
#     depth = 5
#     b1 = make_start_board()

#     t0 = time.perf_counter()
#     naive = perft(b1, depth)
#     t_naive = time.perf_counter() - t0

#     b2 = make_start_board()
#     table = {}
#     t0 = time.perf_counter()
#     hashed = perft_hashed(b2, depth, table)
#     t_hashed = time.perf_counter() - t0

#     # Correctness guard
#     assert hashed == naive, "Hashes must match naive perft"

#     # Print results (pytest -s to see them)
#     print(
#         f"\nperft(depth={depth}): naive={t_naive:.3f}s, hashed={t_hashed:.3f}s"  # noqa: E501
#     )

#     # We expect some speedup
#     assert (
#         t_hashed < t_naive
#     ), f"Expected hashed perft to be faster: {t_hashed:.3f}s vs {t_naive:.3f}s"  # noqa: E501
