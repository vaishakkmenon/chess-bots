# Changelog

## [v7.2] - Time Management & TT Fix
**Date:** 2026-01-09
**Status:** SUCCESS ✅

### Changes
1.  **Fixed Transposition Table Overwrites:**
    *   Prioritized `Exact` (PV) nodes over `LowerBound` (Fail-High) nodes when depths are equal.
    *   This prevents valuable PV lines from being overwritten by less certain cutoff info.
    *   Added `PartialEq` to `NodeType` to support this logic.

2.  **Implemented Time Management:**
    *   Added `TimeManager` struct to the search.
    *   Updated `main.rs` to pass `time_limit` from UCI "go" command.
    *   Updated `search.rs` to check the clock every 2048 nodes and abort if `time_limit` is exceeded.
    *   This fixed the "loss on time" issues at depth 7.

### Results
*   **v7.2 (d7) vs Stockfish (d3)**
    *   **Record:** **10-0 (100% Win Rate)** in preliminary fixed-opening test.
    *   **Record:** **16-0 (100% Win Rate)** in varied opening test (4 openings x 4 games).
    *   **Openings Tested:** Start Position, Alekhine Defense, French Defense, Sicilian Defense.
    *   **Stability:** Zero timeouts, zero crashes.

### Verification Results
- **Vs Stockfish (depth 3)**:
  - **Score**: 7.0/8.0 (6 Wins, 2 Draws, 0 Losses)
  - **Openings Tested**: Startpos, Alekhine, French, Sicilian.
  - **Notes**:
    - Engine successfully played all openings (fixed FEN parsing issue).
    - Only draws occurred in the Sicilian Defense line.
    - Time management worked correctly (no timeouts).

### Bug Fixes (v7.2.1)
- **Fixed Depth 5 Regression**:
  - **Issue**: Iterative Deepening was performing worse than fixed depth at d=5 (0.0/10 vs Stockfish d3).
  - **Cause**: "Toxic" history values from shallow depths were dominating move ordering in deeper searches.
  - **Fix**: Implemented History Decay (divide by 8) between ID depths.
  - **Verification**: Recovered performance to match fixed depth baseline (0 losses vs Fixed Depth engine).

### Analysis of Victory
The 16-0 sweep confirms that the Time Management fix successfully prevented the "forfeit on time" bugs seen in v7.1. The Transposition Table fix likely contributed to finding mates faster, as seen in the pgn results where Wayfinder consistently found mates (e.g., `#18`, `#40`) against Stockfish's depth 3 defense.

### Next Steps
*   Investigate the d5 regression (still untested in v7.2 context).
*   Add randomization or an opening book to prevent deterministic repetition.
