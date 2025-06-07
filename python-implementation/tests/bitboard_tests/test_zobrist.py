from engine.bitboard.board import Board
from engine.bitboard.constants import (
    ZOBRIST_CASTLE_KEYS,
)

# from engine.bitboard.status import is_threefold_repetition


def test_initial_hash_consistency():
    # Two fresh boards should have the same starting hash
    b1 = Board()
    b2 = Board()
    assert b1.zobrist_key == b2.zobrist_key
    # That hash must also match the first entry in history
    assert b1.zobrist_key == b1.zobrist_history[0]


def test_incremental_and_undo_hash_changes():
    b = Board()
    start_hash = b.zobrist_key

    # Make a simple pawn move: e2->e4 (12->28)
    raw = (12, 28, False, None, False, False)
    b.make_move_raw(raw)
    assert b.zobrist_key != start_hash
    # history appended
    assert b.zobrist_history[-1] == b.zobrist_key

    # Undo it: hash should return to start
    b.undo_move_raw()
    assert b.zobrist_key == start_hash
    # history trimmed
    assert b.zobrist_history[-1] == start_hash


def test_castling_hash_variation():
    # Test that castling rights toggle the hash
    b = Board()
    original = b.zobrist_key

    # Simulate removing all castle keys
    b.castling_rights &= ~list(ZOBRIST_CASTLE_KEYS.values())[
        0
    ]  # mask using the first flag
    # Recompute from scratch to isolate castling effect
    b._compute_zobrist_from_scratch()
    assert b.zobrist_key != original


def test_en_passant_hash_variation():
    # Test ep-file keys influence the hash
    b = Board()
    original = b.zobrist_key

    # Manually set an ep square
    b.ep_square = 16  # e.g. square a3 (file=0)
    b._compute_zobrist_from_scratch()
    assert b.zobrist_key != original
    # Changing file (e.g. to b3) should change again
    second = b.zobrist_key
    b.ep_square = 17  # file=1
    b._compute_zobrist_from_scratch()
    assert b.zobrist_key != second


# def test_threefold_repetition_via_hash_history():
#     b = Board()
#     # Starting position is in history once
#     # Append two more identical entries
#     b.zobrist_history.append(b.zobrist_key)
#     b.zobrist_history.append(b.zobrist_key)
#     assert is_threefold_repetition(b)

#     # Only two copies = not yet repetition
#     b2 = Board()
#     b2.zobrist_history.append(b2.zobrist_key)
#     assert not is_threefold_repetition(b2)
