from engine.pgn.tokenizer import tokenize_movetext, TokenType

# TEST CASE PRINTING
# text = "1. e4 e5 {Good move} 2. Nf3 Nc6 $1 1-0"
# toks = tokenize_movetext(text)
# for i, t in enumerate(toks):
#     print(i, t.type, repr(t.text))


def test_basic_tokenizer():
    text = "1. e4 e5 {Good move} 2. Nf3 Nc6 $1 1-0"
    toks = tokenize_movetext(text)
    assert toks[0].type == TokenType.MOVE_NUMBER and toks[0].text == "1."
    assert toks[1].type == TokenType.SAN and toks[1].text == "e4"
    assert toks[3].type == TokenType.COMMENT and "Good move" in toks[3].text
    assert toks[7].type == TokenType.NAG and toks[7].text == "1"
    assert toks[-1].type == TokenType.RESULT and toks[-1].text == "1-0"
