#!/usr/bin/env python3
"""Generate magic numbers, shifts, and attack tables for sliding pieces.

Running this script _once_ populates three source modules that the engine
imports at run-time:

* ``engine/bitboard/magic_constants.py``
* ``engine/bitboard/rook_attack_table.py``
* ``engine/bitboard/bishop_attack_table.py``

After those files exist you normally **do not** run this script again.
Use the ``--force`` flag only when you deliberately change the
relevant-mask definition or discover a bug in the reference attack
generator.
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Tuple

# ---------------------------------------------------------------------------
# Make the project importable when executed as a script
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from engine.bitboard.utils import bit_count, expand_occupancy  # noqa: E402
from engine.bitboard.constants import (  # noqa: E402
    BISHOP_OFFSETS,
    ROOK_OFFSETS,
)

# ---------------------------------------------------------------------------
# Helper: atomic write to avoid half-written files if the process is killed
# ---------------------------------------------------------------------------


def _atomic_write(target: Path, text: str) -> None:
    """Write *text* to *target* atomically (POSIX-safe)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=target.parent
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    shutil.move(tmp_path, target)


# ---------------------------------------------------------------------------
# Reference mask builders (rim-free, as agreed)
# ---------------------------------------------------------------------------


def reference_rook_mask(sq: int) -> int:
    mask = 0
    rank, file = divmod(sq, 8)

    for f in range(file + 1, 7):  # east
        mask |= 1 << (rank * 8 + f)
    for f in range(file - 1, 0, -1):  # west
        mask |= 1 << (rank * 8 + f)
    for r in range(rank + 1, 7):  # north
        mask |= 1 << (r * 8 + file)
    for r in range(rank - 1, 0, -1):  # south
        mask |= 1 << (r * 8 + file)
    return mask


def reference_bishop_mask(sq: int) -> int:
    mask = 0
    rank, file = divmod(sq, 8)

    # NE
    r, f = rank + 1, file + 1
    while r < 7 and f < 7:
        mask |= 1 << (r * 8 + f)
        r += 1
        f += 1
    # NW
    r, f = rank + 1, file - 1
    while r < 7 and f > 0:
        mask |= 1 << (r * 8 + f)
        r += 1
        f -= 1
    # SE
    r, f = rank - 1, file + 1
    while r > 0 and f < 7:
        mask |= 1 << (r * 8 + f)
        r -= 1
        f += 1
    # SW
    r, f = rank - 1, file - 1
    while r > 0 and f > 0:
        mask |= 1 << (r * 8 + f)
        r -= 1
        f -= 1
    return mask


# ---------------------------------------------------------------------------
# Reference attack generators (used to populate tables and to verify magics)
# ---------------------------------------------------------------------------


def _walk_ray(sq: int, offset: int, blockers: int) -> int:
    """Helper for sliding attack generation."""
    mask = 0
    cur = sq
    while True:
        prev_file = cur & 7
        tgt = cur + offset
        if tgt < 0 or tgt >= 64:
            break
        # stop if wrapping on files for horizontal or diagonal moves
        if (offset == 1 and prev_file == 7) or (
            offset == -1 and prev_file == 0
        ):
            break
        if (offset in (9, -7) and prev_file == 7) or (
            offset in (7, -9) and prev_file == 0
        ):
            break
        mask |= 1 << tgt
        if blockers & (1 << tgt):
            break
        cur = tgt
    return mask


def compute_rook_attacks_with_blockers(sq: int, blockers: int) -> int:
    mask = 0
    for offset in ROOK_OFFSETS:
        mask |= _walk_ray(sq, offset, blockers)
    return mask


def compute_bishop_attacks_with_blockers(sq: int, blockers: int) -> int:
    mask = 0
    for offset in BISHOP_OFFSETS:
        mask |= _walk_ray(sq, offset, blockers)
    return mask


# ---------------------------------------------------------------------------
# Magic search helpers
# ---------------------------------------------------------------------------

MASK64 = 0xFFFF_FFFF_FFFF_FFFF


def build_runtime_table(
    mask: int, magic: int, shift: int, subset_table: list[int]
) -> list[int]:
    """Reorder *subset_table* into hash-order using *magic* and *shift*."""
    N = bit_count(mask)
    table_size = 1 << N
    runtime = [0] * table_size
    for subset in range(table_size):
        occ = expand_occupancy(subset, mask)
        idx = ((occ * magic) & MASK64) >> shift
        runtime[idx] = subset_table[subset]
    return runtime


def find_magic(
    sq: int,
    relevant_mask: int,
    attack_table_for_sq: list[int],
    *,
    window: int,
    max_tries: int = 10_000_000,
) -> Tuple[int, int]:
    """Search for a collision-free (magic, shift) pair for *sq*.

    *window* specifies how many shift candidates to try: we test
    ``64-N … 64-N+window-1``.
    """
    N = bit_count(relevant_mask)
    table_size = 1 << N
    blockers = [expand_occupancy(i, relevant_mask) for i in range(table_size)]

    for shift in range(64 - N, 64 - N + window):
        for _ in range(max_tries):
            magic = (
                random.getrandbits(64)
                & random.getrandbits(64)
                & random.getrandbits(64)
            )
            seen: dict[int, int] = {}
            for i in range(table_size):
                idx = ((blockers[i] * magic) & MASK64) >> shift
                prev = seen.get(idx)
                if prev is not None and prev != attack_table_for_sq[i]:
                    break  # collision
                seen[idx] = attack_table_for_sq[i]
            else:
                return magic, shift  # success!
    raise RuntimeError(f"No magic found for square {sq} within search bounds")

# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Build magic constants and attack tables, writing three modules.

    Use ``--force`` to overwrite existing files and ``--seed`` for
    reproducible random numbers.
    """
    ap = argparse.ArgumentParser(
        description="Generate frozen magic tables for sliding pieces."
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing generated modules",
    )
    ap.add_argument(
        "--seed", type=int, default=None, help="RNG seed for reproducibility"
    )
    args = ap.parse_args(argv)

    if args.seed is not None:
        random.seed(args.seed)

    out_dir = Path(__file__).parent
    paths = {
        "const": out_dir / "magic_constants.py",
        "rook": out_dir / "rook_attack_table.py",
        "bishop": out_dir / "bishop_attack_table.py",
    }

    # Abort if tables already exist and --force not supplied
    if not args.force and all(p.exists() for p in paths.values()):
        print("Magic tables already exist. Use --force to regenerate.")
        return

    # --------------------------------------------------------------------
    # Step A: relevant masks
    # --------------------------------------------------------------------
    rel_rook = [reference_rook_mask(sq) for sq in range(64)]
    rel_bish = [reference_bishop_mask(sq) for sq in range(64)]

    # --------------------------------------------------------------------
    # Step B: subset-order attack tables
    # --------------------------------------------------------------------
    rook_subset: list[list[int]] = []
    bishop_subset: list[list[int]] = []

    for sq in range(64):
        # Rook
        mask = rel_rook[sq]
        size = 1 << bit_count(mask)
        tbl = [0] * size
        for subset in range(size):
            blk = expand_occupancy(subset, mask)
            tbl[subset] = compute_rook_attacks_with_blockers(sq, blk)
        rook_subset.append(tbl)

        # Bishop
        mask = rel_bish[sq]
        size = 1 << bit_count(mask)
        tbl = [0] * size
        for subset in range(size):
            blk = expand_occupancy(subset, mask)
            tbl[subset] = compute_bishop_attacks_with_blockers(sq, blk)
        bishop_subset.append(tbl)

    # --------------------------------------------------------------------
    # Step C: magic search + runtime tables
    # --------------------------------------------------------------------
    rook_magics: list[int] = []
    rook_shifts: list[int] = []
    rook_tables: list[list[int]] = []

    bishop_magics: list[int] = []
    bishop_shifts: list[int] = []
    bishop_tables: list[list[int]] = []

    for sq in range(64):
        mask = rel_rook[sq]
        magic, shift = find_magic(sq, mask, rook_subset[sq], window=3)
        rook_magics.append(magic)
        rook_shifts.append(shift)
        rook_tables.append(
            build_runtime_table(mask, magic, shift, rook_subset[sq])
        )
        print(f"Rook   sq {sq:2}: magic 0x{magic:016x} shift {shift}")

    for sq in range(64):
        mask = rel_bish[sq]
        magic, shift = find_magic(sq, mask, bishop_subset[sq], window=2)
        bishop_magics.append(magic)
        bishop_shifts.append(shift)
        bishop_tables.append(
            build_runtime_table(mask, magic, shift, bishop_subset[sq])
        )
        print(f"Bishop sq {sq:2}: magic 0x{magic:016x} shift {shift}")

    # --------------------------------------------------------------------

    # Step D: emit modules atomically
    # --------------------------------------------------------------------
    # 1) magic_constants.py
    const_lines: list[str] = [
        "# Auto-generated by build_magics.py – DO NOT EDIT\n\n",
        "RELEVANT_ROOK_MASKS = [\n",
    ]
    const_lines += [f"    0x{m:016x},\n" for m in rel_rook]
    const_lines.append("]\n\n")

    const_lines.append("RELEVANT_BISHOP_MASKS = [\n")
    const_lines += [f"    0x{m:016x},\n" for m in rel_bish]
    const_lines.append("]\n\n")

    const_lines.append("ROOK_MAGICS = [\n")
    const_lines += [f"    0x{m:016x},\n" for m in rook_magics]
    const_lines.append("]\n\n")

    const_lines.append("ROOK_SHIFTS = [\n")
    const_lines += [f"    {s},\n" for s in rook_shifts]
    const_lines.append("]\n\n")

    const_lines.append("BISHOP_MAGICS = [\n")
    const_lines += [f"    0x{m:016x},\n" for m in bishop_magics]
    const_lines.append("]\n\n")

    const_lines.append("BISHOP_SHIFTS = [\n")
    const_lines += [f"    {s},\n" for s in bishop_shifts]
    const_lines.append("]\n")

    _atomic_write(paths["const"], "".join(const_lines))

    # 2) rook_attack_table.py
    rook_lines: list[str] = [
        "# Auto-generated by build_magics.py – ROOK tables\n\n",
        "ROOK_ATTACK_TABLE = [\n",
    ]
    for tbl in rook_tables:
        rook_lines.append("    [\n")
        rook_lines += [f"        0x{v:016x},\n" for v in tbl]
        rook_lines.append("    ],\n")
    rook_lines.append("]\n")
    _atomic_write(paths["rook"], "".join(rook_lines))

    # 3) bishop_attack_table.py
    bish_lines: list[str] = [
        "# Auto-generated by build_magics.py – BISHOP tables\n\n",
        "BISHOP_ATTACK_TABLE = [\n",
    ]
    for tbl in bishop_tables:
        bish_lines.append("    [\n")
        bish_lines += [f"        0x{v:016x},\n" for v in tbl]
        bish_lines.append("    ],\n")
    bish_lines.append("]\n")
    _atomic_write(paths["bishop"], "".join(bish_lines))

    print("\n✅ Magic tables written successfully.")


if __name__ == "__main__":
    main()
