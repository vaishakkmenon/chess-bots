from engine.bitboard.board import Board
from engine.bitboard.move import Move
from engine.bitboard.constants import (
    WHITE_PAWN,
    BLACK_PAWN,
    WHITE_KNIGHT,
    WHITE,
    BLACK,
)
from engine.bitboard.generator import generate_moves


def sort_moves(moves):
    return sorted(
        moves,
        key=lambda m: (
            m.src,
            m.dst,
            m.capture,
            getattr(m, "en_passant", False),
        ),
    )


def test_generate_moves_white_pawn_pushes_and_captures():
    board = Board()
    board.bitboards = [0] * 12
    # White to move
    board.side_to_move = WHITE

    # pawn on e2 (12), enemy pawns on d3 (19) and f3 (21)
    board.bitboards[WHITE_PAWN] = 1 << 12
    enemy_bb = (1 << 19) | (1 << 21)
    board.bitboards[6] = enemy_bb  # place them as black pawns
    board.update_occupancies()

    moves = generate_moves(board)
    # should have:
    #  - single push e2->e3 (12->20)
    #  - double push e2->e4 (12->28)
    #  - capture d3 (12->19)
    #  - capture f3 (12->21)
    expected = [
        Move(12, 19, capture=True),
        Move(12, 21, capture=True),
        Move(12, 20),
        Move(12, 28),
    ]
    assert sort_moves(moves) == sort_moves(expected)


def test_generate_moves_black_pawn_pushes_and_captures():
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = BLACK

    # pawn on e7 (52), white pawns on d6 (43) and f6 (45)
    board.bitboards[BLACK_PAWN] = 1 << 52
    enemy_bb = (1 << 43) | (1 << 45)
    board.bitboards[0] = enemy_bb  # place them as white pawns
    board.update_occupancies()

    moves = generate_moves(board)
    # should have:
    #  - single push e7->e6 (52->44)
    #  - double push e7->e5 (52->36)
    #  - capture d6 (52->43)
    #  - capture f6 (52->45)
    expected = [
        Move(52, 43, capture=True),
        Move(52, 45, capture=True),
        Move(52, 44),
        Move(52, 36),
    ]
    assert sort_moves(moves) == sort_moves(expected)


def test_generate_moves_knight():
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = WHITE

    # white knight on g1 (sq=6)
    board.bitboards[WHITE_KNIGHT] = 1 << 6
    board.update_occupancies()

    moves = generate_moves(board)
    # g1 -> {e2(12), f3(21), h3(23)}
    expected_dsts = {12, 21, 23}
    got_dsts = {m.dst for m in moves if m.src == 6}
    assert got_dsts == expected_dsts
    # none of these should be captures or en-passant
    assert all(
        not m.capture and not getattr(m, "en_passant", False) for m in moves
    )


def test_generate_moves_en_passant_flow():
    board = Board()
    board.bitboards = [0] * 12
    board.side_to_move = BLACK

    # Set up for black double-push e7->e5
    board.bitboards[BLACK_PAWN] = 1 << 52
    board.update_occupancies()
    board.make_move(Move(src=52, dst=36, capture=False))
    # now side_to_move flipped to WHITE inside make_move
    assert board.side_to_move == WHITE

    # place white pawn on d5 (35) so it can capture ep
    board.bitboards[WHITE_PAWN] = 1 << 35
    board.update_occupancies()

    moves = generate_moves(board)
    # find the en-passant move d5->e6 (35->44)
    ep_moves = [m for m in moves if getattr(m, "en_passant", False)]
    assert ep_moves == [Move(35, 44, capture=True, en_passant=True)]
