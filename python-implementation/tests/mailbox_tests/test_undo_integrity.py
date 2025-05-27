# tests/test_undo_integrity.py
import pytest

from engine.mailbox.board import Board
from engine.mailbox.zobrist import Zobrist
from engine.mailbox.moves.generator import legal_moves

# ──────────────────────────────────────────────────────────────────────────────
# Helpers to build test positions
# ──────────────────────────────────────────────────────────────────────────────


def make_start_board() -> Board:
    b = Board(Zobrist())
    b.init_positions()
    return b


def make_kiwipete_board() -> Board:
    b = Board(Zobrist())
    b.set_fen(
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/"
        "1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    )
    return b


def make_en_passant_board() -> Board:
    """
    Position after 1.e4 d5 2.e5
    FEN: rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR b KQkq e6 0 2
    """
    b = Board(Zobrist())
    b.set_fen("rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR b KQkq e6 0 2")
    return b


def make_promotion_board() -> Board:
    """
    White pawn on h7 ready to promote.
    FEN: 8/7P/8/8/8/8/8/K6k w - - 0 1
    """
    b = Board(Zobrist())
    b.set_fen("8/7P/8/8/8/8/8/K6k w - - 0 1")
    return b


def make_ep_capture_board() -> Board:
    # After: 1.e4 c5 2.e5 d5 3.exd6 e.p.
    b = Board(Zobrist())
    b.set_fen("rnbqkbnr/ppp2ppp/3p4/2P5/8/8/PP2PPPP/RNBQKBNR b KQkq c6 0 3")
    # Black to move, but for undo test we’ll flip to white
    # to exercise the ep-capture
    b.side_to_move = "white"
    return b


# ──────────────────────────────────────────────────────────────────────────────
# Snapshot utility
# ──────────────────────────────────────────────────────────────────────────────


def snapshot(board: Board) -> dict:
    """
    Capture all relevant fields of the board for comparison:
      - squares layout
      - side_to_move
      - halfmove_clock, fullmove_number
      - castling flags, en_passant_target
      - zobrist_hash, history
    """
    return {
        "squares": tuple(tuple(row) for row in board.squares),
        "side": board.side_to_move,
        "halfmove": board.halfmove_clock,
        "fullmove": board.fullmove_number,
        "castle": (
            board.white_can_castle_kingside,
            board.white_can_castle_queenside,
            board.black_can_castle_kingside,
            board.black_can_castle_queenside,
        ),
        "ep": board.en_passant_target,
        "hash": board.zobrist_hash,
        "history": tuple(board.history),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Parameterized positions for undo testing
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "board_builder",
    [
        make_start_board,
        make_kiwipete_board,
        make_en_passant_board,
        make_promotion_board,
        make_ep_capture_board,
    ],
)
def test_undo_integrity_all_moves(board_builder):
    """
    For each legal move in each test position,
    make_move then undo_move should restore the exact board state.
    """
    board = board_builder()
    before = snapshot(board)

    for mv in legal_moves(board, board.side_to_move):
        prev = board.make_move(mv)
        board.undo_move(mv, *prev)
        after = snapshot(board)
        assert after == before, f"Mismatch after undoing move {Board.uci(mv)}"
