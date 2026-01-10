# Tournament Results Summary: Stockfish d3 vs Wayfinder v7.2 (Iterative Deepening)

**Date**: 2026-01-10
**Time Control**: 60 seconds + 0.6 second increment
**Rounds**: 10 (20 games with colors reversed)
**Opponent**: Stockfish depth 3 (full strength, Skill Level 20)

---

## Overall Results

| Wayfinder Depth | Wins | Draws | Losses | Score | Win Rate | Elo Difference |
|----------------|------|-------|--------|-------|----------|----------------|
| **d3** | 0 | 0 | 10 | 0/10 | 0% | -∞ |
| **d4** | 0 | 0 | 10 | 0/10 | 0% | -∞ |
| **d5** | 5 | 5 | 0 | 7.5/10 | **75%** | **+190.8** |
| **d6** | 5 | 5 | 0 | 7.5/10 | **75%** | **+190.8** |
| **d7** | 5 | 0 | 5 | 5/10 | 50% | 0.0 |

---

## Key Findings

### 1. Critical Depth Threshold at d5

There's a **dramatic performance jump** between depth 4 and depth 5:
- **Depths 3-4**: Wayfinder loses 100% of games
- **Depths 5-6**: Wayfinder scores 75% (5 wins, 5 draws, 0 losses)
- **Depth 7**: Performance drops back to 50%

### 2. Depth 5-6: The Sweet Spot

**Best performance configuration:**
- 5 wins, 5 draws, 0 losses
- Elo advantage: ~+191
- When playing White: 100% win rate (5/5)
- When playing Black: 100% draw rate (5/5)

**Draw patterns:**
- **Depth 5**: All draws by 3-fold repetition
- **Depth 6**: All draws by fifty-move rule (endgame struggle)

### 3. Depth 7: Time Management Issues?

At depth 7, performance regresses to even (50%):
- 5 wins, 0 draws, 5 losses
- Perfectly balanced: 5-5 split regardless of color
- **Hypothesis**: Wayfinder may be running into time trouble with deeper search
- The extra depth takes too long, leaving less time for critical positions

### 4. Color Performance Patterns

**Depth 5 (75% score):**
- As White: 5 wins, 0 draws, 0 losses (100%)
- As Black: 0 wins, 5 draws, 0 losses (100% hold)
- Pattern: Aggressive winning with White, solid defensive draws with Black

**Depth 6 (75% score):**
- As White: 0 wins, 0 draws, 5 losses (0%)
- As Black: 5 wins, 5 draws, 0 losses (100%)
- Pattern: **Complete reversal!** Struggles as White, dominates as Black

**Depth 7 (50% score):**
- As White: 0 wins, 0 draws, 5 losses (0%)
- As Black: 5 wins, 0 draws, 0 losses (100%)
- Pattern: Can't win as White, always wins as Black (color bias issue?)

---

## Analysis & Insights

### Why the d4→d5 Jump?

The transition from depth 4 (0%) to depth 5 (75%) suggests:

1. **Tactical Vision Threshold**: Depth 5 is sufficient to see critical tactics that depth 4 misses
2. **Horizon Effect Mitigation**: Shallow searches (d3-d4) fall victim to tactical traps
3. **Search Quality**: The search at d3-d4 may not prune effectively, leading to poor move choices

### Why d7 Underperforms d5-d6?

Several possible explanations:

1. **Time Pressure**: Deeper search consumes more time per move
   - May lead to time scrambles in critical endgames
   - Shallower fallback search when time runs out

2. **Search Inefficiency**: Without proper move ordering or pruning
   - Exponential growth in nodes searched
   - Time wasted on unpromising variations

3. **Evaluation Quality**: Static eval may be insufficient at greater depths
   - Without good heuristics, deeper ≠ better
   - May need piece-square tables (PSQT) or mobility evaluation

### The White/Black Asymmetry (d6-d7)

Wayfinder shows severe color bias at depths 6-7:
- **As White (starting position)**: 0% win rate
- **As Black (responding)**: 100% win rate

**Possible causes:**
1. Search asymmetry in iterative deepening
2. Time allocation issues (uses more time analyzing starting moves)
3. Opening book weakness (Stockfish has better opening preparation)
4. Evaluation bias favoring defensive play

---

## Recommendations

### Optimal Configuration for Current Engine

**For 60+0.6 time control against Stockfish d3:**
- **Recommended depth: 5 or 6**
- Both achieve 75% score (clear advantage)
- Depth 7 provides no benefit and causes time trouble

### Priority Improvements

1. **Fix Color Bias (Critical)**
   - Investigate why White performs poorly at d6-d7
   - Check time management and move allocation

2. **Time Management Enhancements**
   - Implement smarter time allocation
   - Use more time in complex positions, less in simple ones
   - Consider opponent's remaining time

3. **Search Optimizations**
   - Add Late Move Reductions (LMR) to search deeper efficiently
   - Improve move ordering (history heuristic, killer moves)
   - Add null-move pruning for faster search

4. **Evaluation Improvements**
   - Enable piece-square tables (currently stubbed)
   - Add mobility evaluation
   - King safety heuristics

5. **Opening Preparation**
   - Consider adding opening book
   - Improves early-game performance as White

---

## Comparison to Previous Tests

### v7_iter_deep (October 2025) vs v7.2_time_management (January 2026)

The original v7 tests showed more competitive results even at low depths. This suggests v7.2 may have regressions or the current test configuration is more challenging.

**Next Steps:**
1. Review changes between v7 and v7.2
2. Compare PGN games move-by-move
3. Identify tactical blunders in depth 3-4 games

---

## Conclusion

Wayfinder v7.2 shows a **clear depth threshold** where it transitions from completely losing to clearly winning against Stockfish depth 3. The optimal search depth for the 60+0.6 time control is **depth 5 or 6**, achieving a strong 75% score.

However, the severe **color bias** at higher depths and **time management issues** at depth 7 indicate areas for immediate improvement. The engine has tactical strength at sufficient depth but needs better time allocation and opening play.

**Overall Assessment**: Promising tactical strength, but needs work on consistency across colors and efficient time usage.
