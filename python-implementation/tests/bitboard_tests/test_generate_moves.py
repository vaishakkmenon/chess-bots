from engine.bitboard.move import Move
from engine.bitboard.board import Board
from engine.bitboard.utils import move_to_tuple

from engine.bitboard.constants import (
    WHITE,
    BLACK,
    WHITE_KNIGHT,
    WHITE_BISHOP,
    WHITE_PAWN,
    BLACK_PAWN,
    WHITE_ROOK,
    WHITE_QUEEN,
    WHITE_KING,
)
from engine.bitboard.generator import generate_legal_moves


def _rebuild_lookup(board: Board):
    # Rebuild square_to_piece so move-generation + make_move_raw() works
    board.square_to_piece = [None] * 64
    for idx, bb in enumerate(board.bitboards):
        b = bb
        while b:
            lsb = b & -b
            sq = lsb.bit_length() - 1
            board.square_to_piece[sq] = idx
            b ^= lsb


def sort_moves(moves):
    return sorted(
        moves,
        key=lambda m: (m[0], m[1], m[2], m[4]),
    )


def bb_of(idx: int) -> int:
    return 1 << idx


def move_set(moves):
    return {(m[0], m[1], m[2]) for m in moves}


def test_generate_moves_white_pawn_pushes_and_captures():
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    # White pawn on e2 (12), black pawns on d3 (19) and f3 (21)
    board.bitboards[WHITE_PAWN] = 1 << 12
    enemy_bb = (1 << 19) | (1 << 21)
    board.bitboards[BLACK_PAWN] = enemy_bb
    board.update_occupancies()
    _rebuild_lookup(board)

    moves = generate_legal_moves(board)
    expected = [
        move_to_tuple(Move(12, 19, capture=True)),
        move_to_tuple(Move(12, 21, capture=True)),
        move_to_tuple(Move(12, 20)),
        move_to_tuple(Move(12, 28)),
    ]
    assert sort_moves(moves) == sort_moves(expected)


def test_generate_moves_black_pawn_pushes_and_captures():
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = BLACK

    # Black pawn on e7 (52), white pawns on d6 (43) and f6 (45)
    board.bitboards[BLACK_PAWN] = 1 << 52
    enemy_bb = (1 << 43) | (1 << 45)
    board.bitboards[WHITE_PAWN] = enemy_bb
    board.update_occupancies()
    _rebuild_lookup(board)

    moves = generate_legal_moves(board)
    expected = [
        move_to_tuple(Move(52, 43, capture=True)),
        move_to_tuple(Move(52, 45, capture=True)),
        move_to_tuple(Move(52, 44)),
        move_to_tuple(Move(52, 36)),
    ]
    assert sort_moves(moves) == sort_moves(expected)


def test_generate_moves_knight():
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    # White knight on g1 (6)
    board.bitboards[WHITE_KNIGHT] = 1 << 6
    board.update_occupancies()
    _rebuild_lookup(board)

    moves = generate_legal_moves(board)
    # g1 -> {e2(12), f3(21), h3(23)}
    expected_dsts = {12, 21, 23}
    got_dsts = {m[1] for m in moves if m[0] == 6}
    assert got_dsts == expected_dsts
    # None of these should be captures or en passant
    assert all(not m[2] and not m[4] for m in moves)


def test_generate_moves_en_passant_flow():
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = BLACK

    # Black pawn double-push e7->e5
    board.bitboards[BLACK_PAWN] = 1 << 52
    board.update_occupancies()
    _rebuild_lookup(board)

    board.make_move_raw(move_to_tuple(Move(src=52, dst=36, capture=False)))
    assert board.side_to_move == WHITE

    # Place white pawn on d5 (35) to capture en passant
    board.bitboards[WHITE_PAWN] = 1 << 35
    board.update_occupancies()
    _rebuild_lookup(board)

    moves = generate_legal_moves(board)
    ep_moves = [m for m in moves if m[4]]
    assert ep_moves == [
        move_to_tuple(Move(35, 44, capture=True, en_passant=True))
    ]


def test_generate_moves_bishop_simple_and_capture():
    """
    1) Bishop on c1 (2), no blockers ⇒ all quiet diagonals.
    2) Add black pawn on f4 (29) ⇒ bishop can capture at 29 and stops.
    """
    # 1) No-blocker case
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    board.bitboards[WHITE_BISHOP] = bb_of(2)  # c1
    board.update_occupancies()
    _rebuild_lookup(board)

    all_moves = generate_legal_moves(board)
    bishop_moves = [m for m in all_moves if m[0] == 2]
    got = move_set(bishop_moves)
    expected_quiet = {
        (2, 9, False),  # b2
        (2, 16, False),  # a3
        (2, 11, False),  # d2
        (2, 20, False),  # e3
        (2, 29, False),  # f4
        (2, 38, False),  # g5
        (2, 47, False),  # h6
    }
    assert got == expected_quiet

    # 2) Capture case: add black pawn on f4 (29)
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    board.bitboards[WHITE_BISHOP] = bb_of(2)  # c1
    board.bitboards[BLACK_PAWN] = bb_of(29)  # f4
    board.update_occupancies()
    _rebuild_lookup(board)

    all_moves = generate_legal_moves(board)
    bishop_moves = [m for m in all_moves if m[0] == 2]
    got = move_set(bishop_moves)
    expected_with_capture = {
        (2, 9, False),
        (2, 16, False),
        (2, 11, False),
        (2, 20, False),
        (2, 29, True),
    }
    assert got == expected_with_capture


def test_generate_moves_rook_simple_and_capture():
    """
    1) Rook on d4 (27), no blockers ⇒ all quiet rank+file moves.
    2) Add black pawns on d6 (43) and b4 (25) ⇒ captures there and rays stop.
    """
    # 1) No-blocker case
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    board.bitboards[WHITE_ROOK] = bb_of(27)  # d4
    board.update_occupancies()
    _rebuild_lookup(board)

    all_moves = generate_legal_moves(board)
    rook_moves = [m for m in all_moves if m[0] == 27]
    got = move_set(rook_moves)
    expected_quiet = {
        # left
        (27, 26, False),  # c4
        (27, 25, False),  # b4
        (27, 24, False),  # a4
        # right
        (27, 28, False),
        (27, 29, False),
        (27, 30, False),
        (27, 31, False),
        # up
        (27, 35, False),
        (27, 43, False),
        (27, 51, False),
        (27, 59, False),
        # down
        (27, 19, False),
        (27, 11, False),
        (27, 3, False),
    }
    assert got == expected_quiet

    # 2) Capture case: black pawns on d6 (43) and b4 (25)
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    board.bitboards[WHITE_ROOK] = bb_of(27)  # d4
    # place two black pawns
    board.bitboards[BLACK_PAWN] = bb_of(43)  # d6
    board.bitboards[BLACK_PAWN] |= bb_of(25)  # b4
    board.update_occupancies()
    _rebuild_lookup(board)

    all_moves = generate_legal_moves(board)
    rook_moves = [m for m in all_moves if m[0] == 27]
    got = move_set(rook_moves)
    expected_with_capture = {
        # up
        (27, 35, False),
        (27, 43, True),
        # down
        (27, 19, False),
        (27, 11, False),
        (27, 3, False),
        # left
        (27, 26, False),
        (27, 25, True),
        # right
        (27, 28, False),
        (27, 29, False),
        (27, 30, False),
        (27, 31, False),
    }
    assert got == expected_with_capture


def test_generate_moves_queen_simple_and_capture():
    """
    1) Queen on d4 (27), no blockers ⇒ all quiet rook+bishop rays.
    2) Add black pawns on b4 (25) and f6 (45) ⇒ captures and stops correctly.
    """
    # 1) No-blocker case
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    board.bitboards[WHITE_QUEEN] = bb_of(27)  # d4
    board.update_occupancies()
    _rebuild_lookup(board)

    all_moves = generate_legal_moves(board)
    queen_moves = [m for m in all_moves if m[0] == 27]
    got = move_set(queen_moves)

    rook_part = {
        (27, 26, False),
        (27, 25, False),
        (27, 24, False),
        (27, 28, False),
        (27, 29, False),
        (27, 30, False),
        (27, 31, False),
        (27, 35, False),
        (27, 43, False),
        (27, 51, False),
        (27, 59, False),
        (27, 19, False),
        (27, 11, False),
        (27, 3, False),
    }
    bishop_part = {
        (27, 34, False),
        (27, 41, False),
        (27, 48, False),
        (27, 36, False),
        (27, 45, False),
        (27, 54, False),
        (27, 63, False),
        (27, 18, False),
        (27, 9, False),
        (27, 0, False),
        (27, 20, False),
        (27, 13, False),
        (27, 6, False),
    }
    expected_quiet = rook_part.union(bishop_part)
    assert got == expected_quiet

    # 2) Capture case: black pawns on b4 (25) and f6 (45)
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    board.bitboards[WHITE_QUEEN] = bb_of(27)  # d4
    board.bitboards[BLACK_PAWN] = bb_of(25)  # b4
    board.bitboards[BLACK_PAWN] |= bb_of(45)  # f6
    board.update_occupancies()
    _rebuild_lookup(board)

    all_moves = generate_legal_moves(board)
    queen_moves = [m for m in all_moves if m[0] == 27]
    got = move_set(queen_moves)

    expected_with_capture = set()

    # horizontal left: c4(26 quiet), b4(25 capture) stop
    expected_with_capture |= {(27, 26, False), (27, 25, True)}

    # diagonal up-left: c5(34), b6(41), a7(48) all quiet
    expected_with_capture |= {
        (27, 34, False),
        (27, 41, False),
        (27, 48, False),
    }

    # diagonal up-right: e5(36 quiet), f6(45 capture) stop
    expected_with_capture |= {(27, 36, False), (27, 45, True)}

    # horizontal right: e4(28), f4(29), g4(30), h4(31)
    expected_with_capture |= {
        (27, 28, False),
        (27, 29, False),
        (27, 30, False),
        (27, 31, False),
    }

    # vertical up: d5(35), d6(43), d7(51), d8(59)
    expected_with_capture |= {
        (27, 35, False),
        (27, 43, False),
        (27, 51, False),
        (27, 59, False),
    }

    # vertical down: d3(19), d2(11), d1(3)
    expected_with_capture |= {(27, 19, False), (27, 11, False), (27, 3, False)}

    # diagonal down-left: c3(18), b2(9), a1(0)
    expected_with_capture |= {(27, 18, False), (27, 9, False), (27, 0, False)}

    # diagonal down-right: e3(20), f2(13), g1(6)
    expected_with_capture |= {(27, 20, False), (27, 13, False), (27, 6, False)}

    assert got == expected_with_capture


def test_generate_moves_king_simple_and_capture():
    """
    1) King on e1 (4), no blockers ⇒ quiet king moves.
    2) Add black pawns on d1 (3) and f2 (13) ⇒ captures at those squares.
    """
    # 1) No-blocker case
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    board.bitboards[WHITE_KING] = bb_of(4)  # e1
    board.update_occupancies()
    _rebuild_lookup(board)

    all_moves = generate_legal_moves(board)
    king_moves = [m for m in all_moves if m[0] == 4]
    got = move_set(king_moves)
    expected_quiet = {
        (4, 3, False),  # d1
        (4, 5, False),  # f1
        (4, 11, False),  # d2
        (4, 12, False),  # e2
        (4, 13, False),  # f2
    }
    assert got == expected_quiet

    # 2) Capture case: black pawns on d1 (3) and f2 (13)
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    board.bitboards[WHITE_KING] = bb_of(4)  # e1
    board.bitboards[BLACK_PAWN] = bb_of(3)  # d1
    board.bitboards[BLACK_PAWN] |= bb_of(13)  # f2
    board.update_occupancies()
    _rebuild_lookup(board)

    all_moves = generate_legal_moves(board)
    king_moves = [m for m in all_moves if m[0] == 4]
    got = move_set(king_moves)
    expected_with_capture = {
        (4, 3, True),
        (4, 5, False),
        (4, 11, False),
        (4, 12, False),
        (4, 13, True),
    }
    assert got == expected_with_capture
