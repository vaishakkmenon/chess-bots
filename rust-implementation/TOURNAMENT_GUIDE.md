# Chess Engine Tournament Guide

## Overview

This guide explains how to run engine-vs-engine tournaments to test Wayfinder's performance against Stockfish using cutechess-cli.

## Prerequisites

All prerequisites are already installed in the Docker environment:
- ✅ cutechess-cli 1.4.0
- ✅ Stockfish (latest version)
- ✅ Rust toolchain
- ✅ Wayfinder engine (rust-cli)

## Quick Start

### 1. Quick Test (Recommended First)

Run a quick 4-game test to verify everything works:

```bash
cd /workspace/rust-implementation
./test_quick.sh
```

This runs 2 rounds (4 games) between Stockfish depth 3 (full strength) and Wayfinder ID depth 5.

### 2. Full Tournament Suite

Run the complete tournament suite matching the original v7_iter_deep tests:

```bash
cd /workspace/rust-implementation
./test.sh
```

This runs 5 tournaments (depths 3-7) against **full-strength Stockfish**, each with 10 rounds = 20 games per tournament.

### 3. Weakened Opponent Testing (Optional)

For more competitive games and easier wins, test against weakened Stockfish:

```bash
cd /workspace/rust-implementation
./test_weakened.sh
```

This uses Stockfish with **Skill Level 0** (weakest), making it play like a ~1000 ELO player.

## Tournament Configuration

### Original Test Configurations

**v7_iter_deep (October 2025)** - Full strength testing:
- **Stockfish**: Fixed depth 3, Skill Level 20 (default = full strength)
- **Wayfinder v7**: Iterative deepening to depths 3-10
- **Time control**: 60 seconds + 0.6 second increment
- **Games per tournament**: 20 (10 rounds with colors reversed)

**v7.2_time_management (January 2026)** - Weakened opponent:
- **Stockfish**: Fixed depth 3, Skill Level 0 (weakened for competitive games)
- **Wayfinder v7.2**: Iterative deepening to depths 3-7
- **Time control**: Same as above

### Stockfish Skill Level Explained

- **Default**: Level 20 (maximum strength, ~3200 ELO)
- **Range**: 0-20
- **Level 0**: ~1000 ELO (makes deliberate mistakes)
- **Level 10**: ~1600 ELO
- **Level 20**: Full engine strength

Setting Skill Level to 0 causes Stockfish to:
- Occasionally play weak moves
- Create more winnable positions for testing
- Produce games with larger evaluation swings

**Use full strength (Level 20)** for realistic engine comparisons.
**Use weakened (Level 0-10)** for development testing and morale boosts! 😊

### Test Parameters Explained

```bash
cutechess-cli \
  -engine name="Stockfish" cmd=stockfish proto=uci option."Skill Level"=0 depth=3 \
  -engine name="Wayfinder_v7.2" cmd=<path> proto=uci depth=5 \
  -each tc=60+0.6 \
  -rounds 10 \
  -repeat \
  -concurrency 1 \
  -pgnout <output.pgn> \
  -recover
```

**Parameter breakdown:**
- `proto=uci`: Explicitly specify UCI protocol (fixes "Missing chess protocol" warning)
- `option."Skill Level"=N`: Optional - Weakens Stockfish (0 = weakest, 20 = full strength)
- `depth=N`: Fixed search depth for the engine
- `tc=60+0.6`: Time control (60 seconds base + 0.6 increment per move)
- `-rounds 10`: Play 10 game pairs (20 total games)
- `-repeat`: Each opening played twice with reversed colors
- `-concurrency 1`: Run games sequentially (prevents race conditions)
- `-recover`: Restart crashed engines and continue tournament

## Manual Tournament Commands

### Test Against Different Depths

```bash
# Build the engine first
cd /workspace/rust-implementation/rust-cli
cargo build --release

ENGINE_PATH="/workspace/rust-implementation/rust-cli/target/release/rust-cli"

# Stockfish d3 vs Wayfinder d5
cutechess-cli \
  -engine name="Stockfish" cmd=stockfish proto=uci depth=3 \
  -engine name="Wayfinder" cmd="$ENGINE_PATH" proto=uci depth=5 \
  -each tc=60+0.6 \
  -rounds 10 \
  -repeat \
  -pgnout results.pgn
```

### Test with Different Time Controls

**Blitz (3 minutes + 2 second increment):**
```bash
cutechess-cli \
  -engine name="Stockfish" cmd=stockfish proto=uci depth=3 \
  -engine name="Wayfinder" cmd="$ENGINE_PATH" proto=uci depth=6 \
  -each tc=180+2 \
  -rounds 10 \
  -repeat \
  -pgnout blitz_results.pgn
```

**Rapid (10 minutes + 5 second increment):**
```bash
cutechess-cli \
  -engine name="Stockfish" cmd=stockfish proto=uci depth=3 \
  -engine name="Wayfinder" cmd="$ENGINE_PATH" proto=uci depth=7 \
  -each tc=600+5 \
  -rounds 10 \
  -repeat \
  -pgnout rapid_results.pgn
```

### Test With Weakened Stockfish

Add Skill Level option to test against weakened Stockfish for more competitive games:

```bash
cutechess-cli \
  -engine name="Stockfish" cmd=stockfish proto=uci option."Skill Level"=5 depth=5 \
  -engine name="Wayfinder" cmd="$ENGINE_PATH" proto=uci depth=7 \
  -each tc=60+0.6 \
  -rounds 10 \
  -repeat \
  -pgnout weakened_opponent.pgn
```

**Tip:** Adjust Skill Level (0-20) to find a balanced opponent for testing.

## Understanding Results

### Reading PGN Files

Each game in the PGN file contains:
- Game metadata (date, round, players, result)
- Move sequence with evaluation scores and time
- Final result (1-0 = White wins, 0-1 = Black wins, 1/2-1/2 = Draw)

**Example:**
```
[Event "?"]
[White "Wayfinder_v7.2"]
[Black "Stockfish"]
[Result "0-1"]
[TimeControl "60+0.6"]

1. Nc3 {+0.50/3 0.013s} d5 {+0.68/3 0s} ...
```

### Analyzing Tournament Results

```bash
# Count total games
grep -c "^\[Event" results.pgn

# Count wins/losses/draws
grep "^\[Result \"1-0\"\]" results.pgn | wc -l    # White wins
grep "^\[Result \"0-1\"\]" results.pgn | wc -l    # Black wins
grep "^\[Result \"1/2-1/2\"\]" results.pgn | wc -l # Draws
```

### Using External Tools

**Arena Chess GUI** (if available):
- Import PGN files to view games graphically
- Analyze positions with engines
- Compare move quality

**lichess.org/paste**:
- Paste PGN to view games online
- Share results easily

## Troubleshooting

### Issue: "Missing chess protocol" warning

**Solution:** This is a harmless warning. Games still run correctly. The script now explicitly specifies `proto=uci` which should reduce these warnings.

### Issue: "2 opening repetitions vs 1 games per encounter"

**Solution:** This is expected when using `-repeat` flag. It means each opening is played twice (once with each color). This is correct behavior for fair testing.

### Issue: Locale warnings about UTF-8

**Solution:** These Qt warnings are harmless and don't affect tournament results. To suppress them, you can set:
```bash
export LC_ALL=C.UTF-8
./test.sh
```

### Issue: Build fails with feature errors

**Solution:** The rust-cli package doesn't need feature flags. Just use:
```bash
cargo build --release
```

The necessary features (like `load-magic`) are already configured in rust-cli's Cargo.toml dependencies.

## Output Locations

- **Full tournament results**: `/workspace/rust-implementation/rust-engine/src/search/results/v7.2_time_management/`
- **Quick test results**: `/workspace/rust-implementation/rust-engine/src/search/results/v7.2_time_management_test/`

## Customization

### Testing Your Own Positions

Create a custom opening book or EPD file:

```bash
cutechess-cli \
  -engine name="Engine1" ... \
  -engine name="Engine2" ... \
  -openings file=openings.epd format=epd order=random \
  -each tc=60+0.6 \
  -rounds 100
```

### Parallel Execution

For faster tournaments with independent games:

```bash
cutechess-cli \
  ... \
  -concurrency 4 \    # Run 4 games in parallel
  -rounds 100
```

**Note:** Use `-concurrency 1` for deterministic testing and debugging.

## Performance Expectations

Based on iterative deepening:
- **Depth 3**: ~0.01-0.02 seconds per move
- **Depth 5**: ~0.02-0.05 seconds per move
- **Depth 7**: ~0.1-0.5 seconds per move
- **Depth 9**: ~1-10 seconds per move

Higher depths give better play but risk time trouble in fast time controls.

## Next Steps

1. Run the quick test to verify setup
2. Run full tournament suite if quick test succeeds
3. Analyze results to find optimal search depth for your time control
4. Experiment with different time controls and opponent strengths
5. Compare results across different Wayfinder versions

## References

- [cutechess-cli documentation](https://github.com/cutechess/cutechess)
- [UCI protocol specification](https://www.shredderchess.com/download/div/uci.zip)
- Original v7.2 results: `/workspace/rust-implementation/rust-engine/src/search/results/v7.2_time_management/`
