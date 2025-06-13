from __future__ import annotations

from typing import Dict, Tuple

from engine.bitboard.board import Board


def read_epd(text: str) -> Tuple[str, Dict[str, str]]:
    """Parse a single EPD string into a FEN and opcodes."""
    line = text.strip()
    if not line:
        raise ValueError("Empty EPD string")

    parts = line.split()
    if len(parts) < 4:
        raise ValueError("Invalid EPD: missing fields")
    placement, side, castle, ep = parts[:4]
    ops_part = " ".join(parts[4:])

    board = Board()
    board.set_fen(f"{placement} {side} {castle} {ep} 0 1")
    fen = board.get_fen()

    ops: Dict[str, str] = {}
    for raw in ops_part.split(";"):
        item = raw.strip()
        if not item:
            continue
        if " " in item:
            name, val = item.split(None, 1)
        else:
            name, val = item, ""
        ops[name] = val.strip()

    return fen, ops


def write_epd(fen: str, ops: Dict[str, str]) -> str:
    """Serialize a FEN and opcode dictionary back into an EPD string."""
    board = Board()
    board.set_fen(fen)
    fen_fields = board.get_fen().split()
    prefix = " ".join(fen_fields[:4])

    op_tokens = []
    for key, val in ops.items():
        token = key if not val else f"{key} {val}"
        op_tokens.append(f"{token};")

    if op_tokens:
        return prefix + " " + " ".join(op_tokens)
    return prefix
