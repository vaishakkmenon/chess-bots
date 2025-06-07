#!/usr/bin/env python3
# Usage:
#   python3 engine/bitboard/gen_zobrist.py > engine/bitboard/zobrist_keys.txt
#   Copy from zobrist_output.txt to engine/bitboard/constants.py

import random


def rand64():
    return random.getrandbits(64)


def main():
    # 1) Piece-square keys (12×64)
    piece_keys = [[rand64() for _ in range(64)] for __ in range(12)]

    # 2) Side-to-move key
    side_key = rand64()

    # 3) Castling-rights keys
    castle_keys = {
        "K": rand64(),
        "Q": rand64(),
        "k": rand64(),
        "q": rand64(),
    }

    # 4) En-passant file keys
    ep_keys = [rand64() for _ in range(8)]

    # Now pretty-print
    print("# Zobrist hash constants (auto-generated)")
    print("ZOBRIST_PIECE_KEYS = [")
    for row in piece_keys:
        print("    [")
        for k in row:
            print(f"        0x{k:016x},")
        print("    ],")
    print("]")
    print()
    print(f"ZOBRIST_SIDE_KEY = 0x{side_key:016x}")
    print()
    print("ZOBRIST_CASTLE_KEYS = {")
    for flag, key in castle_keys.items():
        print(f"    '{flag}': 0x{key:016x},")
    print("}")
    print()
    print("ZOBRIST_EP_KEYS = [")
    for k in ep_keys:
        print(f"    0x{k:016x},")
    print("]")


if __name__ == "__main__":
    main()
