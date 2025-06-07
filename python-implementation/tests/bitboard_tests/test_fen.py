import pytest
from engine.bitboard.board import Board

# Common FEN strings for testing
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
EMPTY_FEN = "8/8/8/8/8/8/8/8 w - - 0 1"
CUSTOM_FEN = "r3k2r/8/4p3/8/3P4/8/8/R3K2R b KQkq d6 15 42"


@pytest.mark.parametrize("fen", [STARTING_FEN, EMPTY_FEN, CUSTOM_FEN])
def test_set_and_get_fen_roundtrip(fen):
    """
    Ensure that set_fen correctly parses a FEN string and get_fen
    serializes it back to the identical string.
    """
    board = Board()
    board.set_fen(fen)
    output = board.get_fen()
    assert output == fen


def test_invalid_fen_raises():
    """
    Invalid FEN strings should raise a ValueError.
    """
    board = Board()
    with pytest.raises(ValueError):
        board.set_fen("invalid fen string")


@pytest.mark.parametrize(
    "fen, expected_ep",
    [
        ("8/8/8/8/3Pp3/8/8/8 w - e6 0 1", "e6"),
        ("8/8/8/8/8/8/8/8 b - - 0 1", "-"),
    ],
)
def test_ep_square_handling(fen, expected_ep):
    """
    Test that en-passant square is correctly parsed and serialized.
    """
    board = Board()
    board.set_fen(fen)
    output = board.get_fen()
    parts = output.split()
    # en-passant square is the 4th field
    assert parts[3] == expected_ep


@pytest.mark.parametrize(
    "fen, half, full",
    [
        ("8/8/8/8/8/8/8/8 w - - 0 1", 0, 1),
        ("8/8/8/8/8/8/8/8 w - - 99 100", 99, 100),
    ],
)
def test_halfmove_fullmove_fields(fen, half, full):
    """
    Verify that halfmove and fullmove counters
    are parsed and serialized correctly.
    """
    board = Board()
    board.set_fen(fen)
    assert board.halfmove_clock == half
    assert board.fullmove_number == full
    # Check round-trip
    output = board.get_fen()
    parts = output.split()
    assert int(parts[4]) == half
    assert int(parts[5]) == full
