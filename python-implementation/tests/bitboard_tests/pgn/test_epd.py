from engine.bitboard.board import Board
from engine.pgn.epd import read_epd, write_epd


def test_read_epd_basic():
    text = (
        "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR b KQkq e3 "
        'bm dxe3; id "example";'
    )
    fen, ops = read_epd(text)

    board = Board()
    board.set_fen(
        "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    )
    expected_fen = board.get_fen()

    assert fen == expected_fen
    assert ops["bm"] == "dxe3"
    assert ops["id"] == '"example"'


def test_epd_round_trip():
    text = '8/8/8/8/8/8/8/8 w - - bm a4; id "Empty";'
    fen, ops = read_epd(text)
    out = write_epd(fen, ops)
    assert out == text
