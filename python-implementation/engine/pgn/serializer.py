from __future__ import annotations
from typing import List, TYPE_CHECKING
from engine.pgn.parser import rawmove_to_san
from engine.bitboard.board import Board

if TYPE_CHECKING:
    from engine.pgn.game import PGNGame


def serialize_pgn(game: PGNGame, line_length: int = 80) -> str:
    """
    Convert a PGNGame back into PGN text.
    """
    out_lines: List[str] = []

    # 1) Headers
    for tag, val in game.tags.items():
        out_lines.append(f'[{tag} "{val}"]')
    out_lines.append("")  # blank line

    # 2) Movetext assembly with replay
    board = Board()
    tokens: List[str] = []
    for i, move in enumerate(game.moves):
        # Prepend move number on White’s turn
        if i % 2 == 0:
            num = (i // 2) + 1
            tokens.append(f"{num}.")
        # Get SAN in this position
        san = rawmove_to_san(board, move)
        tokens.append(san)

        # Attach comments or NAGs keyed by fullmove number
        fullmove = (i // 2) + 1
        if fullmove in game.comments and i % 2 == 1:
            tokens.append(f"{{{game.comments[fullmove]}}}")

        if fullmove in game.nags and i % 2 == 1:
            for nag in game.nags[fullmove]:
                tokens.append(f"${nag}")

        # Apply the move to update board
        board.make_move_raw(move)

    # 3) Result
    tokens.append(game.tags.get("Result", "*"))

    # 4) Join movetext (no wrapping for now)
    out_lines.append(" ".join(tokens))

    # 5) Final newline
    return "\n".join(out_lines) + "\n"
