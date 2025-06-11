import re
from enum import Enum
from typing import List
from dataclasses import dataclass


class TokenType(Enum):
    MOVE_NUMBER = "MOVE_NUMBER"  # e.g. “1.” or “1...”
    SAN = "SAN"  # e.g. “Nf3”, “exd6”, “O-O”
    COMMENT = "COMMENT"  # e.g. “{This is good}”
    NAG = "NAG"  # e.g. “$1”
    RESULT = "RESULT"  # “1-0”, “½-½”, “0-1”, “*”


@dataclass
class Token:
    type: TokenType
    text: str


# \d+\. → digits + dot (e.g. “1.”); (\.\.)? → optional “..” for Black (e.g. “1...”) # noqa: E501
MOVE_NUM_RE = re.compile(r"^\d+\.(\.\.)?$")
# \$\d+    → dollar sign + one or more digits (e.g. “$1”)
NAG_RE = re.compile(r"^\$\d+$")
# matches exactly “1-0”, “0-1”, “1/2-1/2”, or “*”
RESULT_RE = re.compile(r"^(1-0|0-1|1/2-1/2|\*)$")
# \{.*\}   → braces around any content (greedy) for comments
COMMENT_RE = re.compile(r"^\{.*\}$")

MASTER_RE = re.compile(
    r"\{[^}]*\}|\d+\.\.\.|\d+\.|\$\d+|1-0|0-1|1/2-1/2|\*|\S+"
)


def tokenize_movetext(text: str) -> List[Token]:
    tokens: List[Token] = []
    for raw in MASTER_RE.findall(text):
        if MOVE_NUM_RE.match(raw):
            tokens.append(Token(TokenType.MOVE_NUMBER, raw))
        elif COMMENT_RE.match(raw):
            tokens.append(Token(TokenType.COMMENT, raw[1:-1]))  # strip { }
        elif NAG_RE.match(raw):
            tokens.append(Token(TokenType.NAG, raw[1:]))  # strip $
        elif RESULT_RE.match(raw):
            tokens.append(Token(TokenType.RESULT, raw))
        else:
            tokens.append(Token(TokenType.SAN, raw))
    return tokens
