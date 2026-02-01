#!/usr/bin/env python3
"""
Extract draws and losses for Wayfinder from a PGN file.

Usage: python extract_failures.py <input.pgn> [output.pgn]

If output is not specified, creates <input>_failures.pgn
"""

import sys
import re
from pathlib import Path


def parse_games(pgn_content: str) -> list[dict]:
    """Parse PGN content into list of games with headers and moves."""
    games = []
    current_game = {"headers": {}, "moves": "", "raw": ""}
    lines = pgn_content.split("\n")
    in_moves = False
    game_start = 0

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith("["):
            if in_moves and current_game["headers"]:
                # End of previous game
                current_game["raw"] = "\n".join(lines[game_start:i])
                games.append(current_game)
                current_game = {"headers": {}, "moves": "", "raw": ""}
                game_start = i

            in_moves = False
            # Parse header
            match = re.match(r'\[(\w+)\s+"(.*)"\]', line)
            if match:
                current_game["headers"][match.group(1)] = match.group(2)
        elif line and not line.startswith("["):
            in_moves = True
            current_game["moves"] += line + "\n"

    # Don't forget the last game
    if current_game["headers"]:
        current_game["raw"] = "\n".join(lines[game_start:])
        games.append(current_game)

    return games


def is_wayfinder_loss(game: dict) -> bool:
    """Check if Wayfinder lost this game."""
    white = game["headers"].get("White", "")
    black = game["headers"].get("Black", "")
    result = game["headers"].get("Result", "")

    # Wayfinder as White, lost (0-1)
    if "Wayfinder" in white and result == "0-1":
        return True
    # Wayfinder as Black, lost (1-0)
    if "Wayfinder" in black and result == "1-0":
        return True
    return False


def is_draw(game: dict) -> bool:
    """Check if the game was a draw."""
    return game["headers"].get("Result", "") == "1/2-1/2"


def format_game(game: dict) -> str:
    """Format a game back to PGN."""
    lines = []
    for key, value in game["headers"].items():
        lines.append(f'[{key} "{value}"]')
    lines.append("")
    lines.append(game["moves"].strip())
    lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_failures.py <input.pgn> [output.pgn]")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    # Default output filename
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        output_file = input_file.parent / f"{input_file.stem}_failures.pgn"

    # Read and parse
    print(f"Reading: {input_file}")
    content = input_file.read_text()
    games = parse_games(content)

    # Categorize
    losses = []
    draws = []
    wins = 0

    for game in games:
        if is_wayfinder_loss(game):
            losses.append(game)
        elif is_draw(game):
            draws.append(game)
        else:
            wins += 1

    # Summary
    total = len(games)
    print(f"\n=== Results Summary ===")
    print(f"Total games: {total}")
    print(f"Wayfinder wins: {wins}")
    print(f"Wayfinder losses: {len(losses)}")
    print(f"Draws: {len(draws)}")
    print(f"Win rate: {wins/total*100:.1f}%")

    # Write failures
    failures = losses + draws
    if failures:
        output_lines = []
        separator = ";" + "=" * 79 + "\n"
        section_separator = "\n\n" + ";" + "#" * 79 + "\n" + ";" + "#" * 79 + "\n\n"

        # Add losses first
        if losses:
            output_lines.append(separator)
            output_lines.append(f";  WAYFINDER LOSSES ({len(losses)} games)\n")
            output_lines.append(f";  These are games where Wayfinder was checkmated or resigned\n")
            output_lines.append(separator)
            output_lines.append("\n")

            for i, game in enumerate(losses, 1):
                white = game["headers"].get("White", "")
                black = game["headers"].get("Black", "")
                result = game["headers"].get("Result", "")
                round_num = game["headers"].get("Round", "?")
                ply_count = game["headers"].get("PlyCount", "?")
                output_lines.append(f"; --- LOSS #{i} ---\n")
                output_lines.append(f"; Round {round_num}: {white} vs {black} = {result} ({ply_count} ply)\n")
                output_lines.append(format_game(game))
                output_lines.append("\n\n")

        # Add section break between losses and draws
        if losses and draws:
            output_lines.append(section_separator)

        # Add draws
        if draws:
            output_lines.append(separator)
            output_lines.append(f";  DRAWS ({len(draws)} games)\n")
            output_lines.append(f";  These are games that ended in stalemate, repetition, or 50-move rule\n")
            output_lines.append(separator)
            output_lines.append("\n")

            for i, game in enumerate(draws, 1):
                white = game["headers"].get("White", "")
                black = game["headers"].get("Black", "")
                round_num = game["headers"].get("Round", "?")
                ply_count = game["headers"].get("PlyCount", "?")
                termination = ""
                # Check for 50-move or repetition in the moves
                moves_lower = game["moves"].lower()
                if "50" in game["moves"] or "fifty" in moves_lower:
                    termination = " [50-move rule]"
                elif "repetition" in moves_lower:
                    termination = " [Repetition]"
                elif "stalemate" in moves_lower:
                    termination = " [Stalemate]"
                output_lines.append(f"; --- DRAW #{i} ---\n")
                output_lines.append(f"; Round {round_num}: {white} vs {black}{termination} ({ply_count} ply)\n")
                output_lines.append(format_game(game))
                output_lines.append("\n\n")

        output_file.write_text("".join(output_lines))
        print(f"\nFailures written to: {output_file}")
    else:
        print("\nNo failures found! Perfect score!")

    return len(losses), len(draws)


if __name__ == "__main__":
    main()
