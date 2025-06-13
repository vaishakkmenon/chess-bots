# engine/uci.py

"""Minimal UCI interface backed by the bitboard engine."""

from __future__ import annotations

import sys
from typing import Optional

from engine.bitboard.board import Board
from engine.bitboard.perft import perft_count


def main() -> None:
    board: Optional[Board] = Board()
    for raw in sys.stdin:
        cmd = raw.strip()
        if not cmd:
            continue
        parts = cmd.split()
        token = parts[0]

        if token == "uci":
            print("id name chess-bots")
            print("id author Vaishak Menon")
            print("uciok")
        elif token == "isready":
            print("readyok")
        elif token == "position":
            if len(parts) >= 2 and parts[1] == "startpos":
                board = Board()
            elif len(parts) >= 8 and parts[1] == "fen":
                fen = " ".join(parts[2:8])
                board = Board()
                board.set_fen(fen)
        elif token == "go" and len(parts) == 3 and parts[1] == "depth":
            if board is not None:
                depth = int(parts[2])
                nodes = perft_count(board, depth)
                print(f"info nodes {nodes}")
                print("bestmove 0000")
        elif token in {"quit", "stop"}:
            break
        sys.stdout.flush()


if __name__ == "__main__":
    main()
