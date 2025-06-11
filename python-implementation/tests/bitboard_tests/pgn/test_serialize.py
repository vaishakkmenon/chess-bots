from engine.pgn.parser import read_pgn
from engine.pgn.serializer import serialize_pgn

SIMPLE_PGN = """[Event "Test"]
[Site "Nowhere"]
[Date "2025.06.08"]
[Round "1"]
[White "A"]
[Black "B"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 {Ruy Lopez opening} 4. Ba4 Nf6 $1 1-0
"""


def test_serialize_round_trip():
    # Parse the sample
    game = read_pgn(SIMPLE_PGN)
    # Serialize back to PGN text
    out = serialize_pgn(game)

    # Check headers preserved
    assert '[Event "Test"]' in out
    assert '[Site "Nowhere"]' in out
    assert '[Result "1-0"]' in out

    # Check movetext content
    assert "1. e4 e5" in out
    assert "3. Bb5 a6 {Ruy Lopez opening}" in out
    assert "4. Ba4 Nf6 $1" in out

    # Check trailing result
    assert out.strip().endswith("1-0")

    # Optionally: round-trip parse again and compare moves count
    game2 = read_pgn(out)
    assert len(game2.moves) == len(game.moves)
    assert game2.comments == game.comments
    assert game2.nags == game.nags
