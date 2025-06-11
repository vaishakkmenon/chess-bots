from typing import List, Dict
from engine.bitboard.config import RawMove  # noqa: TC002


class PGNGame:
    def __init__(
        self,
        tags: Dict[str, str],
        moves: List[RawMove],
        comments: Dict[int, str],
        nags: Dict[int, List[int]],
    ):
        self.tags = tags
        self.moves = moves
        self.comments = comments
        self.nags = nags

    @property
    def result(self) -> str:
        return self.tags.get("Result", "*")
