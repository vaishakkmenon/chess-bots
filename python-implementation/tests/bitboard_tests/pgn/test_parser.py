import pytest
from engine.pgn.game import PGNGame
from engine.bitboard.board import Board
from engine.pgn.parser import san_to_rawmove, SanParsingError, read_pgn


def test_san_knight_basic():
    board = Board()  # starting position
    move = san_to_rawmove(board, "Nf3")
    # In the initial position, g1→f3 is the only Nf3:
    assert move[0] == 6  # src square index for g1
    assert move[1] == 21  # dst index for f3


def test_san_pawn_capture():
    # Set up a position where exd6 is legal
    board = Board()
    board.set_fen(
        "rnbqkbnr/ppp1pppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 2"
    )
    move = san_to_rawmove(board, "dxe3")
    assert move[2] is True  # capture flag
    assert move[4] is True  # en_passant flag


def test_san_castling():
    board = Board()
    board.set_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    move_o_o = san_to_rawmove(board, "O-O")
    assert move_o_o[5] is True  # castling flag
    move_o_o_o = san_to_rawmove(board, "O-O-O")
    assert move_o_o_o[5] is True  # castling flag


def test_san_ambiguous_error():
    board = Board()
    # FEN with only a king on e1 and knights on b1,f1 so both can jump to d2
    fen = "8/8/8/8/8/8/1N2K1N1/8 w - - 0 1"
    board.set_fen(fen)

    # Both Nb1→d2 and Nf1→d2 are legal: san_to_rawmove should raise
    with pytest.raises(SanParsingError):
        san_to_rawmove(board, "Nd2")


SIMPLE_PGN = """[Event "Test"]
[Site "Nowhere"]
[Date "2025.06.08"]
[Round "1"]
[White "A"]
[Black "B"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 {Ruy Lopez opening} 4. Ba4 Nf6 $1 1-0
"""


def test_read_pgn_basics():
    game = read_pgn(SIMPLE_PGN)
    assert isinstance(game, PGNGame)
    # tags
    assert game.tags["Event"] == "Test"
    assert game.tags["Result"] == "1-0"
    # moves should be 8 plies
    assert len(game.moves) == 8
    # a comment on ply 3 (after move 4.Ba4)
    assert game.comments[3] == "Ruy Lopez opening"
    # a NAG ($1) on ply 4
    assert game.nags[4] == [1]
