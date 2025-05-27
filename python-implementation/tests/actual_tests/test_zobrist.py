import pytest
from engine.board import Board
from engine.moves.move import Move
from engine.zobrist import (
    Zobrist,
    PIECE_ORDER,
    CASTLING_RIGHTS,
    EN_PASSANT_FILES,
)

MAX_64BIT = 2**64 - 1


@pytest.fixture(scope="module")
def zobrist():
    return Zobrist()


@pytest.fixture
def board(zobrist):
    b = Board(zobrist)
    b.init_positions()
    b.side_to_move = "white"
    b.zobrist_hash = b.zobrist.compute_hash(b, b.side_to_move)
    return b


def test_compute_hash_consistency(zobrist):
    board = Board(zobrist)
    board.init_positions()

    hash_white_1 = zobrist.compute_hash(board, "white")
    hash_white_2 = zobrist.compute_hash(board, "white")
    assert (
        hash_white_1 == hash_white_2
    ), "Hashes for same position/side should match"

    hash_black_1 = zobrist.compute_hash(board, "black")
    hash_black_2 = zobrist.compute_hash(board, "black")
    assert (
        hash_black_1 == hash_black_2
    ), "Hashes for same position/side should match"

    assert (
        hash_white_1 != hash_black_1
    ), "Hashes for different side to move should differ"


def test_piece_square_table_size(zobrist):
    assert len(zobrist.piece_square) == len(
        PIECE_ORDER
    ), "Should have 12 piece types"
    for piece_row in zobrist.piece_square:
        assert len(piece_row) == 64, "Each piece must have 64 squares"


def test_castling_rights_table_size(zobrist):
    assert set(zobrist.castling_rights.keys()) == set(
        CASTLING_RIGHTS
    ), "Castling rights keys mismatch"
    for val in zobrist.castling_rights.values():
        assert isinstance(val, int), "Castling rights values must be int"
        assert 0 <= val <= MAX_64BIT, "Castling rights values out of range"


def test_en_passant_table_size(zobrist):
    assert set(zobrist.en_passant.keys()) == set(
        EN_PASSANT_FILES
    ), "En passant keys mismatch"
    for val in zobrist.en_passant.values():
        assert isinstance(val, int), "En passant values must be int"
        assert 0 <= val <= MAX_64BIT, "En passant values out of range"


def test_side_to_move_value(zobrist):
    val = zobrist.side_to_move
    assert isinstance(val, int), "Side to move must be int"
    assert 0 <= val <= MAX_64BIT, "Side to move value out of range"


def test_reproducibility():
    z1 = Zobrist()
    z2 = Zobrist()

    for p in range(len(PIECE_ORDER)):
        for sq in range(64):
            assert (
                z1.piece_square[p][sq] == z2.piece_square[p][sq]
            ), "Piece-square values differ"

    for key in CASTLING_RIGHTS:
        assert (
            z1.castling_rights[key] == z2.castling_rights[key]
        ), "Castling rights values differ"

    for file in EN_PASSANT_FILES:
        assert (
            z1.en_passant[file] == z2.en_passant[file]
        ), "En passant values differ"

    assert z1.side_to_move == z2.side_to_move, "Side to move values differ"


def test_make_undo_move_hash_consistency(board: Board):
    initial_hash = board.zobrist_hash

    move = Move((5, 2), (5, 4))
    castling_rights, halfmove_clock = board.make_move(move)
    moved_hash = board.zobrist_hash

    board.undo_move(move, castling_rights, halfmove_clock)
    undone_hash = board.zobrist_hash

    assert (
        initial_hash == undone_hash
    ), f"Hash mismatch after make/undo: {initial_hash:#x} != {undone_hash:#x}"
    assert initial_hash != moved_hash, "Hash did not change after move"


def test_hash_changes_on_capture(board: Board):
    move1 = Move((5, 2), (5, 4))
    cr1, hm1 = board.make_move(move1)

    move2 = Move((4, 7), (4, 5))
    cr2, hm2 = board.make_move(move2)

    move3 = Move((5, 4), (4, 5))
    cr3, hm3 = board.make_move(move3)

    hash_after_capture = board.zobrist_hash

    board.undo_move(move3, cr3, hm3)
    hash_after_undo_capture = board.zobrist_hash

    assert (
        hash_after_capture != board.zobrist_hash
    ), "Hash did not change after capture move"
    assert (
        hash_after_undo_capture == board.zobrist_hash
    ), "Hash did not revert correctly after undo capture"

    board.undo_move(move2, cr2, hm2)
    board.undo_move(move1, cr1, hm1)


def test_hash_changes_on_castling(board: Board):
    board.init_positions()
    board[(6, 1)] = Board.EMPTY
    board[(7, 1)] = Board.EMPTY

    initial_hash = board.zobrist_hash

    move = Move((5, 1), (7, 1))
    cr, hm = board.make_move(move)

    after_castle_hash = board.zobrist_hash

    board.undo_move(move, cr, hm)

    after_undo_hash = board.zobrist_hash

    assert (
        initial_hash != after_castle_hash
    ), "Hash did not change after castling"
    assert (
        initial_hash == after_undo_hash
    ), "Hash did not revert after undoing castling"


@pytest.mark.parametrize("promo_piece", ["Q", "R", "B", "N"])
def test_promotion_hash_consistency(board: Board, promo_piece: str):
    board.init_positions()
    for file in range(1, 9):
        for rank in range(1, 9):
            board[(file, rank)] = Board.EMPTY
    board[(5, 7)] = "P"

    initial_hash = board.zobrist_hash

    move = Move((5, 7), (5, 8), promo_piece)
    cr, hm = board.make_move(move)
    hash_after_promo = board.zobrist_hash

    board.undo_move(move, cr, hm)
    hash_after_undo = board.zobrist_hash

    assert (
        initial_hash != hash_after_promo
    ), "Hash should change after promotion"
    assert (
        initial_hash == hash_after_undo
    ), "Hash should revert after undoing promotion"


@pytest.mark.parametrize(
    "castling_move",
    [
        Move((5, 1), (7, 1)),
        Move((5, 1), (3, 1)),
        Move((5, 8), (7, 8)),
        Move((5, 8), (3, 8)),
    ],
)
def test_castling_hash_consistency(board: Board, castling_move: Move):
    board.init_positions()
    rank = castling_move.from_sq[1]
    if castling_move.to_sq[0] > castling_move.from_sq[0]:
        board[(6, rank)] = Board.EMPTY
        board[(7, rank)] = Board.EMPTY
    else:
        board[(2, rank)] = Board.EMPTY
        board[(3, rank)] = Board.EMPTY
        board[(4, rank)] = Board.EMPTY

    initial_hash = board.zobrist_hash

    cr, hm = board.make_move(castling_move)
    hash_after_castle = board.zobrist_hash

    board.undo_move(castling_move, cr, hm)
    hash_after_undo = board.zobrist_hash

    assert (
        initial_hash != hash_after_castle
    ), "Hash should change after castling"
    assert (
        initial_hash == hash_after_undo
    ), "Hash should revert after undoing castling"


def test_en_passant_hash_consistency(board: Board):
    board.init_positions()
    start_hash = board.zobrist_hash  # ↙ hash of the initial position

    # 1.  ♙ e2→e4
    m1 = Move((5, 2), (5, 4))
    cr1, hm1 = board.make_move(m1)

    # 1…  ♞ g8→f6  (any quiet move by Black to keep things simple)
    m2 = Move((7, 8), (6, 6))
    cr2, hm2 = board.make_move(m2)

    # 2.  ♙ e4→e5   (white pawn reaches 5th rank)
    m3 = Move((5, 4), (5, 5))
    cr3, hm3 = board.make_move(m3)

    # 2…  ♙ d7→d5   (two-square pawn push, enabling e.p.)
    m4 = Move((4, 7), (4, 5))
    cr4, hm4 = board.make_move(m4)

    pre_ep_hash = board.zobrist_hash  # hash *before* the capture

    # 3.  ♙ e5×d6 e.p.
    ep = Move((5, 5), (4, 6))
    ep.is_en_passant = True
    cr5, hm5 = board.make_move(ep)

    hash_after_ep = board.zobrist_hash
    assert pre_ep_hash != hash_after_ep, "Hash should change after en-passant"

    # ─── undo all moves in reverse order ───
    board.undo_move(ep, cr5, hm5)  # undo capture
    board.undo_move(m4, cr4, hm4)  # undo d7d5
    board.undo_move(m3, cr3, hm3)  # undo e4e5
    board.undo_move(m2, cr2, hm2)  # undo knight move
    board.undo_move(m1, cr1, hm1)  # undo e2e4

    final_hash = board.zobrist_hash
    assert (
        final_hash == start_hash
    ), "Hash must revert to the original position after all undos"


def test_initial_position_hash_stability(board: Board):
    board.init_positions()
    hash1 = board.zobrist_hash
    for _ in range(5):
        hash2 = board.zobrist.compute_hash(board, "white")
        assert hash1 == hash2, "Initial position hash should be stable"


def test_random_move_sequence_hash_consistency(board: Board):
    board.init_positions()

    moves_to_make = [
        Move((5, 2), (5, 4)),
        Move((5, 7), (5, 5)),
        Move((6, 1), (5, 3)),
        Move((6, 8), (5, 6)),
    ]

    initial_hash = board.zobrist_hash
    history = []

    for move in moves_to_make:
        cr, hm = board.make_move(move)
        history.append((move, cr, hm))

    for move, cr, hm in reversed(history):
        board.undo_move(move, cr, hm)

    undone_hash = board.zobrist_hash

    assert (
        initial_hash == undone_hash
    ), "Hash should revert after undoing all moves"
