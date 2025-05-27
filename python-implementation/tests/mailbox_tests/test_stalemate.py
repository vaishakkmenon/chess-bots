import pytest

from engine.mailbox.board import Board
from engine.mailbox.zobrist import Zobrist
from engine.mailbox.status import is_stalemate

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def zobrist():
    return Zobrist()


def make_board(pieces: dict[tuple[int, int], str], zobrist: Zobrist) -> Board:
    """
    Build an otherwise-empty board from a {(file, rank): "piece"} map.
    Files/ranks are 1-based (a1 == (1, 1), h8 == (8, 8)).
    Upper-case = White, lower-case = Black.
    """
    b = Board(zobrist)
    for sq, pc in pieces.items():
        b[sq] = pc
    b._update_castling_from_board()
    # Initialize Zobrist hash after position setup
    b.zobrist_hash = b.zobrist.compute_hash(
        b, "white"
    )  # or "black" depending on test case side
    return b


# ---------------------------------------------------------------------------
# Test matrix
# ---------------------------------------------------------------------------

TEST_POSITIONS = [
    # ────────────────────────────────────────────────────────────────────
    # ★★★  TRUE stalemates  ★★★
    # ────────────────────────────────────────────────────────────────────
    # 1. Classic corner: Ka8 boxed by Qb6 & Kc6
    (
        {
            (3, 6): "K",  # White king  c6
            (2, 6): "Q",  # White queen b6
            (1, 8): "k",  # Black king  a8
        },
        "black",
        True,
        "Ka8 boxed by Qb6 + Kc6",
    ),
    # 2. Edge cage: Kh8 frozen by Qg6 & Kf7
    (
        {
            (6, 7): "K",  # White king  f7
            (7, 6): "Q",  # White queen g6
            (8, 8): "k",  # Black king  h8
        },
        "black",
        True,
        "Kh8 stalemated by Qg6 + Kf7",
    ),
    # 3. Diagonal block: Kh1 boxed by Qg3 & Kf2   (your earlier “mate” case)
    (
        {
            (7, 3): "Q",  # White queen g3
            (6, 2): "K",  # White king  f2
            (8, 1): "k",  # Black king  h1
        },
        "black",
        True,
        "Kh1 stalemated by Qg3 + Kf2",
    ),
    # ────────────────────────────────────────────────────────────────────
    # ★★★  FALSE-positive guards  ★★★
    # ────────────────────────────────────────────────────────────────────
    # 4. Knight+pawn *check* (king is in check, therefore NOT stalemate)
    (
        {
            (8, 1): "K",  # White king  h1  (in check!)
            (6, 3): "k",  # Black king  f3
            (7, 3): "n",  # Black knight g3
            (7, 2): "p",  # Black pawn   g2
        },
        "white",
        False,
        "Knight+pawn gives check -> not stalemate",
    ),
    # 5. R+K vs K – White still has rook moves (not stalemate)
    (
        {
            (1, 1): "k",  # Black king  a1
            (3, 3): "R",  # White rook  c3
            (2, 3): "K",  # White king  b3
        },
        "white",
        False,
        "White rook can move -> not stalemate",
    ),
    # 6. “Under-promotion rescue”:  b-pawn can still promote to N/B/R/Q
    (
        {
            (2, 7): "P",  # White pawn b7 (can push or promote)
            (3, 8): "k",  # Black king c8
            (1, 6): "K",  # White king a6 (blocks own king moves)
        },
        "white",
        False,
        "Pawn promotion available -> not stalemate",
    ),
]


@pytest.mark.parametrize(
    "pieces, side, expect_stalemate, label", TEST_POSITIONS
)
def test_stalemate_variations(pieces, side, expect_stalemate, label, zobrist):
    board = make_board(pieces, zobrist)
    assert is_stalemate(board, side) is expect_stalemate, label
