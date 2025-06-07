from engine.pgn.headers import parse_pgn_headers

DEF_HEADER_BLOCK = [
    '[Event "My Game"]',
    '[Site "My City"]',
    '[Date "2025.06.07"]',
    '[Round "1"]',
    '[White "Alice"]',
    '[Black "Bob"]',
    '[Result "1-0"]',
    "",
    "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0",
]


def test_parse_standard_headers():
    tags = parse_pgn_headers(DEF_HEADER_BLOCK)
    assert tags["Event"] == "My Game"
    assert tags["Site"] == "My City"
    assert tags["Date"] == "2025.06.07"
    assert tags["Round"] == "1"
    assert tags["White"] == "Alice"
    assert tags["Black"] == "Bob"
    assert tags["Result"] == "1-0"


def test_duplicate_tags_last_wins():
    lines = ['[Event "First"]', '[Event "Second"]', ""]
    tags = parse_pgn_headers(lines)
    assert tags["Event"] == "Second"


def test_malformed_tag_ignored():
    lines = [
        '[Event "Good"]',
        "[BadTag MissingQuote]",
        '[Site "AlsoGood"]',
        "",
    ]
    tags = parse_pgn_headers(lines)
    assert "Site" not in tags  # because we break on the malformed line
