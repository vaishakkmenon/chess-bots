#!/usr/bin/env python3
"""
PGN Analysis Script for Wayfinder vs Crafty
Analyzes hallucinations, king safety, opening performance, and win patterns
"""

import re
from dataclasses import dataclass
from typing import List, Tuple, Optional
from collections import defaultdict


@dataclass
class Move:
    """Represents a single move with evaluation"""
    move_number: int
    ply: int
    move_text: str
    eval_cp: Optional[int]  # Evaluation in centipawns
    depth: Optional[int]
    time: Optional[float]
    is_book: bool


@dataclass
class Game:
    """Represents a complete game"""
    white: str
    black: str
    result: str
    moves: List[Move]
    ply_count: int

    def wayfinder_color(self) -> Optional[str]:
        """Returns 'white' or 'black' if Wayfinder played, else None"""
        if self.white == "Wayfinder":
            return "white"
        elif self.black == "Wayfinder":
            return "black"
        return None

    def wayfinder_won(self) -> bool:
        """Returns True if Wayfinder won"""
        color = self.wayfinder_color()
        if color == "white":
            return self.result == "1-0"
        elif color == "black":
            return self.result == "0-1"
        return False

    def wayfinder_lost(self) -> bool:
        """Returns True if Wayfinder lost"""
        color = self.wayfinder_color()
        if color == "white":
            return self.result == "0-1"
        elif color == "black":
            return self.result == "1-0"
        return False

    def get_wayfinder_eval(self, move: Move) -> Optional[int]:
        """
        Get evaluation from Wayfinder's perspective
        Positive = Wayfinder winning, Negative = Wayfinder losing
        """
        if move.eval_cp is None:
            return None

        color = self.wayfinder_color()
        if color is None:
            return None

        # Move evals are from side-to-move perspective
        # If it's Wayfinder's move, eval is already from their perspective
        # If it's opponent's move, we need to flip
        is_wayfinder_move = (color == "white" and move.ply % 2 == 1) or \
                           (color == "black" and move.ply % 2 == 0)

        if is_wayfinder_move:
            return move.eval_cp
        else:
            return -move.eval_cp


def parse_eval_comment(comment: str) -> Tuple[Optional[int], Optional[int], Optional[float], bool]:
    """
    Parse evaluation comment from PGN
    Returns: (eval_cp, depth, time, is_book)

    Examples:
    - "{book}" -> (None, None, None, True)
    - "{+0.15/10 0.3s}" -> (15, 10, 0.3, False)
    - "{-0.12/11 0.52s}" -> (-12, 11, 0.52, False)
    - "{-M6/7 0.10s}" -> (-30000, 7, 0.10, False)  # Mate in 6
    """
    comment = comment.strip()

    if comment == "{book}":
        return (None, None, None, True)

    # Match mate scores: {-M6/7 0.10s} or {+M4/3 0.059s}
    mate_match = re.match(r'\{([+-]?)M(\d+)/(\d+)\s+([\d.]+)s', comment)
    if mate_match:
        sign, mate_in, depth, time = mate_match.groups()
        # Convert mate to large centipawn value
        eval_cp = 30000 if sign != '-' else -30000
        return (eval_cp, int(depth), float(time), False)

    # Match regular evals: {+0.15/10 0.3s} or {-0.12/11 0.52s}
    match = re.match(r'\{([+-]?[\d.]+)/(\d+)\s+([\d.]+)s', comment)
    if match:
        eval_str, depth, time = match.groups()
        eval_cp = int(float(eval_str) * 100)  # Convert to centipawns
        return (eval_cp, int(depth), float(time), False)

    # Match mate announcements: {-327.66/4 0s, Black mates}
    mate_announce = re.match(r'\{([+-]?[\d.]+)/(\d+)\s+([\d.]+)s,', comment)
    if mate_announce:
        eval_str, depth, time = mate_announce.groups()
        eval_cp = int(float(eval_str) * 100)
        return (eval_cp, int(depth), float(time), False)

    return (None, None, None, False)


def parse_pgn(filename: str) -> List[Game]:
    """Parse PGN file and return list of games"""
    with open(filename, 'r') as f:
        content = f.read()

    games = []
    game_texts = content.strip().split('\n\n[Event')

    for i, game_text in enumerate(game_texts):
        if i > 0:
            game_text = '[Event' + game_text

        if not game_text.strip():
            continue

        # Extract headers
        white_match = re.search(r'\[White "(.+?)"\]', game_text)
        black_match = re.search(r'\[Black "(.+?)"\]', game_text)
        result_match = re.search(r'\[Result "(.+?)"\]', game_text)
        plycount_match = re.search(r'\[PlyCount "(\d+)"\]', game_text)

        if not (white_match and black_match and result_match):
            continue

        white = white_match.group(1)
        black = black_match.group(1)
        result = result_match.group(1)
        ply_count = int(plycount_match.group(1)) if plycount_match else 0

        # Extract moves
        # Find the line after headers (moves start after blank line)
        lines = game_text.split('\n')
        move_lines = []
        in_moves = False
        for line in lines:
            if in_moves:
                move_lines.append(line)
            elif line.strip() == '':
                in_moves = True

        move_text = ' '.join(move_lines)

        # Parse moves with evaluations
        moves = []
        ply = 0

        # Match patterns like: 1. Nf3 {book} or 1. e4 {+0.15/10 0.3s}
        pattern = r'(\d+)\.\s*(\S+)\s*(\{[^}]+\})?(?:\s*(\S+)\s*(\{[^}]+\})?)?'

        for match in re.finditer(pattern, move_text):
            move_number = int(match.group(1))

            # White's move
            white_move = match.group(2)
            white_comment = match.group(3) or ""

            if white_move and not white_move.startswith('{'):
                ply += 1
                eval_cp, depth, time, is_book = parse_eval_comment(white_comment)
                moves.append(Move(
                    move_number=move_number,
                    ply=ply,
                    move_text=white_move,
                    eval_cp=eval_cp,
                    depth=depth,
                    time=time,
                    is_book=is_book
                ))

            # Black's move
            black_move = match.group(4)
            black_comment = match.group(5) or ""

            if black_move and not black_move.startswith('{'):
                ply += 1
                eval_cp, depth, time, is_book = parse_eval_comment(black_comment)
                moves.append(Move(
                    move_number=move_number,
                    ply=ply,
                    move_text=black_move,
                    eval_cp=eval_cp,
                    depth=depth,
                    time=time,
                    is_book=is_book
                ))

        games.append(Game(
            white=white,
            black=black,
            result=result,
            moves=moves,
            ply_count=ply_count
        ))

    return games


def analyze_hallucinations(games: List[Game]) -> dict:
    """Analyze games where Wayfinder lost but had positive evaluation"""
    results = {
        'losses_with_eval_gt_100': 0,
        'losses_with_eval_gt_200': 0,
        'top_hallucinations': [],
        'top_non_mate_hallucinations': []
    }

    hallucinations = []  # (game_idx, peak_eval, move_at_peak)
    non_mate_hallucinations = []  # Exclude obvious mate-eval bugs

    for game_idx, game in enumerate(games):
        if not game.wayfinder_lost():
            continue

        peak_eval = None
        peak_move = None
        peak_non_mate_eval = None
        peak_non_mate_move = None
        had_eval_gt_100 = False
        had_eval_gt_200 = False

        for move in game.moves:
            wf_eval = game.get_wayfinder_eval(move)
            if wf_eval is None:
                continue

            if wf_eval > 100:
                had_eval_gt_100 = True
            if wf_eval > 200:
                had_eval_gt_200 = True

            # Track all-time peak
            if peak_eval is None or wf_eval > peak_eval:
                peak_eval = wf_eval
                peak_move = move

            # Track peak excluding mate scores (> 250.00)
            if wf_eval < 25000:
                if peak_non_mate_eval is None or wf_eval > peak_non_mate_eval:
                    peak_non_mate_eval = wf_eval
                    peak_non_mate_move = move

        if had_eval_gt_100:
            results['losses_with_eval_gt_100'] += 1
        if had_eval_gt_200:
            results['losses_with_eval_gt_200'] += 1

        if peak_eval and peak_eval > 0:
            hallucinations.append((game_idx, peak_eval, peak_move, game))

        if peak_non_mate_eval and peak_non_mate_eval > 0:
            non_mate_hallucinations.append((game_idx, peak_non_mate_eval,
                                           peak_non_mate_move, game))

    # Sort by peak eval (worst hallucinations first)
    hallucinations.sort(key=lambda x: x[1], reverse=True)
    non_mate_hallucinations.sort(key=lambda x: x[1], reverse=True)

    results['top_hallucinations'] = hallucinations[:3]
    results['top_non_mate_hallucinations'] = non_mate_hallucinations[:5]

    return results


def analyze_king_safety_collapses(games: List[Game]) -> dict:
    """Find moves where eval dropped > 1.50 in one move"""
    results = {
        'total_collapses': 0,
        'collapses_with_enemy_pressure': 0,
        'collapse_details': []
    }

    for game_idx, game in enumerate(games):
        if game.wayfinder_color() is None:
            continue

        prev_eval = None

        for i, move in enumerate(game.moves):
            wf_eval = game.get_wayfinder_eval(move)

            if wf_eval is None or prev_eval is None:
                prev_eval = wf_eval
                continue

            # Check for eval drop > 150 centipawns
            drop = prev_eval - wf_eval

            if drop > 150:
                results['total_collapses'] += 1

                # For now, we can't check piece positions without FEN parsing
                # This would require reconstructing board state from moves
                # We'll note this as a limitation

                results['collapse_details'].append({
                    'game_idx': game_idx,
                    'move_number': move.move_number,
                    'ply': move.ply,
                    'move_text': move.move_text,
                    'eval_before': prev_eval,
                    'eval_after': wf_eval,
                    'drop': drop,
                    'wayfinder_color': game.wayfinder_color()
                })

            prev_eval = wf_eval

    return results


def analyze_opening_performance(games: List[Game]) -> dict:
    """Calculate average evaluation at move 10"""
    results = {
        'games_analyzed': 0,
        'total_eval_at_move_10': 0,
        'avg_eval_at_move_10': 0,
        'has_opening_deficit': False
    }

    evals = []

    for game in games:
        if game.wayfinder_color() is None:
            continue

        # Find ply 20 (after move 10 by both sides)
        for move in game.moves:
            if move.ply == 20:
                wf_eval = game.get_wayfinder_eval(move)
                if wf_eval is not None:
                    evals.append(wf_eval)
                break

    if evals:
        results['games_analyzed'] = len(evals)
        results['total_eval_at_move_10'] = sum(evals)
        results['avg_eval_at_move_10'] = sum(evals) / len(evals)
        results['has_opening_deficit'] = results['avg_eval_at_move_10'] < -30

    return results


def analyze_wins(games: List[Game]) -> dict:
    """Analyze Wayfinder's wins"""
    results = {
        'total_wins': 0,
        'avg_move_count': 0,
        'positional_wins': 0,
        'tactical_wins': 0,
        'win_details': []
    }

    winning_games = []

    for game_idx, game in enumerate(games):
        if not game.wayfinder_won():
            continue

        results['total_wins'] += 1
        move_count = len([m for m in game.moves if not m.is_book]) // 2
        winning_games.append(move_count)

        # Check for sudden eval jumps > 2.0 (200 cp)
        is_tactical = False
        prev_eval = None

        for move in game.moves:
            wf_eval = game.get_wayfinder_eval(move)

            if wf_eval is None or prev_eval is None:
                prev_eval = wf_eval
                continue

            gain = wf_eval - prev_eval

            if gain > 200:
                is_tactical = True
                break

            prev_eval = wf_eval

        if is_tactical:
            results['tactical_wins'] += 1
        else:
            results['positional_wins'] += 1

        results['win_details'].append({
            'game_idx': game_idx,
            'move_count': move_count,
            'win_type': 'tactical' if is_tactical else 'positional'
        })

    if winning_games:
        results['avg_move_count'] = sum(winning_games) / len(winning_games)

    return results


def generate_report(games: List[Game], hallucinations: dict, collapses: dict,
                   opening: dict, wins: dict):
    """Generate comprehensive analysis report"""

    print("=" * 80)
    print("WAYFINDER vs CRAFTY - PGN ANALYSIS REPORT")
    print("=" * 80)
    print()

    # Overall statistics
    total_games = len(games)
    wayfinder_games = sum(1 for g in games if g.wayfinder_color() is not None)
    wayfinder_wins = sum(1 for g in games if g.wayfinder_won())
    wayfinder_losses = sum(1 for g in games if g.wayfinder_lost())
    wayfinder_draws = sum(1 for g in games if g.wayfinder_color() and
                         g.result == "1/2-1/2")

    print(f"Total Games: {total_games}")
    print(f"Wayfinder Games: {wayfinder_games}")
    print(f"Wayfinder Record: {wayfinder_wins}W - {wayfinder_losses}L - {wayfinder_draws}D")
    if wayfinder_games > 0:
        win_rate = (wayfinder_wins / wayfinder_games) * 100
        print(f"Win Rate: {win_rate:.1f}%")
    print()

    # 1. HALLUCINATIONS
    print("=" * 80)
    print("1. HALLUCINATION ANALYSIS")
    print("=" * 80)
    print()
    print("A hallucination occurs when Wayfinder thought it was winning (+eval)")
    print("but eventually lost the game.")
    print()
    print(f"Losses with eval > +1.00 at any point: {hallucinations['losses_with_eval_gt_100']}")
    print(f"Losses with eval > +2.00 at any point: {hallucinations['losses_with_eval_gt_200']}")
    print()

    if hallucinations['top_hallucinations']:
        print("TOP 3 WORST HALLUCINATIONS (including mate-eval bugs):")
        print()
        for rank, (game_idx, peak_eval, peak_move, game) in enumerate(hallucinations['top_hallucinations'], 1):
            # Determine whose move it was
            is_white_move = peak_move.ply % 2 == 1
            move_side = "White" if is_white_move else "Black"
            wayfinder_color = game.wayfinder_color()
            was_wayfinder_move = (wayfinder_color == "white" and is_white_move) or \
                                (wayfinder_color == "black" and not is_white_move)

            is_mate_eval = abs(peak_eval) > 25000
            eval_type = " [MATE EVAL BUG!]" if is_mate_eval else ""

            print(f"#{rank} - Game {game_idx + 1}")
            print(f"    Peak Evaluation: +{peak_eval/100:.2f} (Wayfinder winning){eval_type}")
            print(f"    At Move: {peak_move.move_number}. {peak_move.move_text}")
            print(f"    Move by: {move_side} ({'Wayfinder' if was_wayfinder_move else 'Crafty'})")
            print(f"    Ply: {peak_move.ply}")
            print(f"    Wayfinder playing as: {wayfinder_color.upper()}")
            print(f"    Final Result: {game.result} (Wayfinder LOST)")

            # Show a few moves around the peak for context
            print(f"    Context (moves {max(1, peak_move.move_number-2)} to {peak_move.move_number+2}):")
            for m in game.moves:
                if abs(m.move_number - peak_move.move_number) <= 2:
                    wf_eval = game.get_wayfinder_eval(m)
                    eval_str = f"{wf_eval/100:+.2f}" if wf_eval is not None else "N/A"
                    marker = " <<<" if m == peak_move else ""
                    print(f"        {m.move_number}. {m.move_text} ({eval_str}){marker}")
            print()

    if hallucinations['top_non_mate_hallucinations']:
        print()
        print("TOP 5 NON-MATE HALLUCINATIONS (real position miseval):")
        print()
        for rank, (game_idx, peak_eval, peak_move, game) in enumerate(hallucinations['top_non_mate_hallucinations'], 1):
            # Determine whose move it was
            is_white_move = peak_move.ply % 2 == 1
            move_side = "White" if is_white_move else "Black"
            wayfinder_color = game.wayfinder_color()
            was_wayfinder_move = (wayfinder_color == "white" and is_white_move) or \
                                (wayfinder_color == "black" and not is_white_move)

            print(f"#{rank} - Game {game_idx + 1}")
            print(f"    Peak Evaluation: +{peak_eval/100:.2f}")
            print(f"    At Move: {peak_move.move_number}. {peak_move.move_text}")
            print(f"    Move by: {move_side} ({'Wayfinder' if was_wayfinder_move else 'Crafty'})")
            print(f"    Wayfinder playing as: {wayfinder_color.upper()}")

            # Show a few moves around the peak for context
            print(f"    Context (moves {max(1, peak_move.move_number-2)} to {peak_move.move_number+2}):")
            for m in game.moves:
                if abs(m.move_number - peak_move.move_number) <= 2:
                    wf_eval = game.get_wayfinder_eval(m)
                    eval_str = f"{wf_eval/100:+.2f}" if wf_eval is not None else "N/A"
                    marker = " <<<" if m == peak_move else ""
                    print(f"        {m.move_number}. {m.move_text} ({eval_str}){marker}")
            print()

    # 2. KING SAFETY COLLAPSES
    print("=" * 80)
    print("2. KING SAFETY COLLAPSE ANALYSIS")
    print("=" * 80)
    print()
    print(f"Total Collapses (eval drop > 1.50): {collapses['total_collapses']}")
    print()

    if collapses['collapse_details']:
        print("LARGEST COLLAPSES:")
        print()
        # Sort by drop amount
        sorted_collapses = sorted(collapses['collapse_details'],
                                 key=lambda x: x['drop'], reverse=True)

        for i, collapse in enumerate(sorted_collapses[:5], 1):
            print(f"#{i} - Game {collapse['game_idx'] + 1}, Move {collapse['move_number']}")
            print(f"    Move: {collapse['move_text']}")
            print(f"    Eval Before: {collapse['eval_before']/100:+.2f}")
            print(f"    Eval After: {collapse['eval_after']/100:+.2f}")
            print(f"    Drop: {collapse['drop']/100:.2f}")
            print(f"    Wayfinder: {collapse['wayfinder_color'].upper()}")
            print()

    print("NOTE: Enemy piece position analysis requires FEN reconstruction,")
    print("which is not implemented in this version of the script.")
    print()

    # 3. OPENING PERFORMANCE
    print("=" * 80)
    print("3. OPENING PERFORMANCE ANALYSIS")
    print("=" * 80)
    print()
    print(f"Games with data at move 10: {opening['games_analyzed']}")
    if opening['games_analyzed'] > 0:
        avg_eval = opening['avg_eval_at_move_10'] / 100
        print(f"Average eval at move 10: {avg_eval:+.2f}")
        print(f"Opening book deficit: {'YES' if opening['has_opening_deficit'] else 'NO'}")
        print()
        if opening['has_opening_deficit']:
            print("⚠ Wayfinder is consistently behind after opening!")
        else:
            print("✓ Wayfinder's opening is competitive")
    print()

    # 4. WIN ANALYSIS
    print("=" * 80)
    print("4. WIN ANALYSIS")
    print("=" * 80)
    print()
    print(f"Total Wins: {wins['total_wins']}")
    if wins['total_wins'] > 0:
        print(f"Average Move Count: {wins['avg_move_count']:.1f}")
        print(f"Positional Wins: {wins['positional_wins']} ({wins['positional_wins']/wins['total_wins']*100:.1f}%)")
        print(f"Tactical Wins: {wins['tactical_wins']} ({wins['tactical_wins']/wins['total_wins']*100:.1f}%)")
        print()
        print("Win Type Breakdown:")
        for detail in wins['win_details'][:10]:  # Show first 10
            print(f"  Game {detail['game_idx'] + 1}: {detail['move_count']} moves ({detail['win_type']})")
    print()

    # 5. FINDINGS AND RECOMMENDATIONS
    print("=" * 80)
    print("5. FINDINGS AND RECOMMENDATIONS")
    print("=" * 80)
    print()

    # Calculate key metrics
    hallucination_rate = 0
    if wayfinder_losses > 0:
        hallucination_rate = (hallucinations['losses_with_eval_gt_100'] /
                             wayfinder_losses * 100)

    print("KEY FINDINGS:")
    print()

    if hallucination_rate > 50:
        print(f"⚠ HIGH HALLUCINATION RATE: {hallucination_rate:.1f}% of losses")
        print("  → Evaluation function is overoptimistic")
        print("  → Consider: More conservative eval, better king safety")
        print()

    if collapses['total_collapses'] > 10:
        print(f"⚠ FREQUENT EVAL COLLAPSES: {collapses['total_collapses']} instances")
        print("  → Wayfinder missing tactical shots")
        print("  → Consider: Deeper search, tactical pattern recognition")
        print()

    if opening['has_opening_deficit']:
        print("⚠ OPENING DEFICIT DETECTED")
        print("  → Consider: Opening book, better early-game eval")
        print()

    if wins['total_wins'] > 0:
        tactical_ratio = wins['tactical_wins'] / wins['total_wins']
        if tactical_ratio > 0.7:
            print(f"✓ STRONG TACTICAL PLAY: {tactical_ratio*100:.0f}% of wins are tactical")
            print("  → Wayfinder excels at exploiting blunders")
            print()
        elif tactical_ratio < 0.3:
            print(f"✓ POSITIONAL STRENGTH: {(1-tactical_ratio)*100:.0f}% of wins are positional")
            print("  → Wayfinder can grind out advantages")
            print()

    print("RECOMMENDATIONS:")
    print()
    print("1. Evaluation Calibration:")
    print("   - Review eval function for overoptimism")
    print("   - Increase king safety weight")
    print("   - Add pawn structure penalties")
    print()
    print("2. Tactical Awareness:")
    print("   - Increase search depth in critical positions")
    print("   - Add quiescence search extensions")
    print("   - Implement tactical pattern recognition")
    print()
    print("3. Opening Preparation:")
    print("   - Expand opening book")
    print("   - Tune early-game piece-square tables")
    print("   - Focus on solid, defensive openings")
    print()
    print("=" * 80)


def main():
    """Main analysis function"""
    pgn_file = "/workspace/rust-implementation/bench_arena/wayfinder_vs_crafty.pgn"

    print("Parsing PGN file...")
    games = parse_pgn(pgn_file)
    print(f"Parsed {len(games)} games")
    print()

    print("Analyzing hallucinations...")
    hallucinations = analyze_hallucinations(games)

    print("Analyzing king safety collapses...")
    collapses = analyze_king_safety_collapses(games)

    print("Analyzing opening performance...")
    opening = analyze_opening_performance(games)

    print("Analyzing wins...")
    wins = analyze_wins(games)

    print()
    print("Generating report...")
    print()

    generate_report(games, hallucinations, collapses, opening, wins)


if __name__ == "__main__":
    main()
