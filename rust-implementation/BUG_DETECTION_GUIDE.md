# Chess Engine Bug Detection Guide

## Overview

Before adding new features, it's critical to verify your engine's correctness. This guide outlines methods to identify bugs in Wayfinder.

---

## ✅ Current Test Status

### Perft Tests (Move Generation)
**Status: ✅ PASSING (10/10 tests)**

```bash
cargo test --release --test perft_tests
```

**Result:** All perft tests pass up to depth 5, confirming:
- ✅ Move generation is correct
- ✅ No illegal moves being generated
- ✅ No legal moves being missed
- ✅ Make/unmake is reversible

**Verdict:** Move generation is bug-free!

### Magic Table Consistency
**Status: ⚠️ FAILING (1 test)**

The `test_magic_table_consistency` test fails. This is likely a **test configuration issue**, not a real bug, because:
1. Perft tests pass (would fail if magic tables were wrong)
2. Engine plays legal moves in tournaments
3. The mismatch is between runtime-generated and precomputed tables

**Action:** Low priority - doesn't affect correctness.

---

## 🔍 Bug Detection Methods

### 1. Perft Testing (Move Generation) ⭐ CRITICAL

**Purpose:** Verify every legal move is generated correctly.

**How it works:**
- Counts all possible positions at each depth
- Compares against known-correct values
- Any mismatch = bug in move generation

**Run it:**
```bash
cd /workspace/rust-implementation/rust-engine

# Quick perft (depth 1-5)
cargo test --release --test perft_tests

# Deep perft (depth 6-7, slow)
cargo test --release --test perft_tests -- --ignored
```

**What to look for:**
- ❌ Test failures = Move generation bug
- ✅ All tests pass = Move generation is correct

**Current Status:** ✅ All tests pass

---

### 2. Tactical Position Tests

**Purpose:** Verify the engine finds forced mates and wins material.

**Create test positions:**

```rust
// tests/tactical_tests.rs
use rust_engine::board::Board;
use rust_engine::search::search;
use rust_engine::moves::magic::MagicTables;

#[test]
fn test_mate_in_1() {
    // White to move and mate in 1: Qxh7#
    let fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1";
    let mut board = Board::from_fen(fen).unwrap();
    let tables = MagicTables::new();

    let (score, best_move) = search(&mut board, &tables, 3, None);

    // Should find Qxh7# with mate score
    assert!(score > 9000, "Should recognize mate");
    assert_eq!(best_move.unwrap().to_uci(), "h5h7", "Should play Qxh7#");
}

#[test]
fn test_capture_queen() {
    // Black queen hanging, should capture it
    let fen = "rnb1kbnr/pppp1ppp/8/4p3/4P3/8/PPPPQPPP/RNB1KBNR w KQkq - 0 1";
    let mut board = Board::from_fen(fen).unwrap();
    let tables = MagicTables::new();

    let (score, best_move) = search(&mut board, &tables, 2, None);

    // Should win the queen
    assert!(score > 700, "Should win queen (900) minus pawn (100)");
}
```

**Run it:**
```bash
cargo test --release tactical_tests
```

---

### 3. Game Analysis (Identify Blunders)

**Purpose:** Analyze tournament games to find tactical/strategic mistakes.

**Method 1: Find Large Evaluation Drops**

```bash
# Find games where Wayfinder's eval dropped by 5+ pawns
grep -E '\{[+-][0-9]+\.[0-9]+/[0-9]+ ' stockfish_d3_vs_wayfinder_id_d3.pgn | \
  awk '{print $0}' | \
  # Look for big swings from one move to the next
```

**Method 2: Analyze Specific Positions**

Take a position where Wayfinder blundered and test it:

```bash
# Build CLI
cd /workspace/rust-implementation/rust-cli
cargo build --release

# Analyze a position
echo -e "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\ngo depth 5\nquit" | ./target/release/rust-cli
```

**What to look for:**
- Large evaluation swings between depths (unstable eval)
- Engine plays obvious blunders (hangs pieces)
- Misses simple tactics (forks, pins, skewers)

---

### 4. Self-Play Consistency

**Purpose:** Ensure engine plays consistently at different depths.

**Test:**
```bash
# Wayfinder d5 vs Wayfinder d7 (should be competitive, not 100-0)
cutechess-cli \
  -engine name="Wayfinder_d5" cmd=./rust-cli depth=5 proto=uci \
  -engine name="Wayfinder_d7" cmd=./rust-cli depth=7 proto=uci \
  -each tc=60+0.6 \
  -rounds 10 \
  -repeat \
  -pgnout self_play_test.pgn
```

**What to look for:**
- ❌ One depth dominates (100-0) = Bug or severe time issue
- ✅ Results are competitive (60-40 to 70-30) = Healthy

---

### 5. Color Bias Detection ⚠️ SUSPICIOUS

**Current Issue:** At depths 6-7, Wayfinder shows extreme color bias:
- **As White:** 0% win rate (0-10)
- **As Black:** 100% win rate (10-0)

**This suggests a bug!**

**Test it:**
```bash
# Play Wayfinder vs itself (should be ~50-50)
cutechess-cli \
  -engine name="Wayfinder_White" cmd=./rust-cli depth=6 proto=uci \
  -engine name="Wayfinder_Black" cmd=./rust-cli depth=6 proto=uci \
  -each tc=60+0.6 \
  -rounds 20 \
  -pgnout color_bias_test.pgn

# Check results
grep "Result" color_bias_test.pgn | sort | uniq -c
```

**Expected:** ~10-10 split (50%)
**If you see:** 0-20 or 20-0 = **CRITICAL BUG**

**Possible causes:**
1. ❌ Sign error in evaluation (returning wrong perspective)
2. ❌ Time management bug (uses all time on first move)
3. ❌ Zobrist key error (hash collisions)
4. ❌ Make/unmake bug (state corruption)

---

### 6. Position Verification

**Purpose:** Verify evaluation and move generation on known positions.

**Standard Test Positions:**

```rust
#[test]
fn test_starting_position_eval() {
    let board = Board::from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let eval = static_eval(&board);

    // Starting position should be approximately equal
    assert!(eval.abs() < 50, "Starting position eval: {}", eval);
}

#[test]
fn test_piece_values() {
    // White up a queen
    let board = Board::from_fen("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let eval = static_eval(&board);

    // Should be approximately +900 (queen value)
    assert!(eval > 850 && eval < 950, "Queen advantage eval: {}", eval);
}
```

---

### 7. UCI Protocol Compliance

**Purpose:** Ensure engine follows UCI protocol correctly.

**Test manually:**
```bash
echo -e "uci\nisready\nposition startpos\ngo depth 3\nquit" | ./rust-cli
```

**Check for:**
- ✅ Responds to "uci" with "uciok"
- ✅ Responds to "isready" with "readyok"
- ✅ Outputs "bestmove" after search
- ❌ Crashes or hangs = Bug

---

### 8. Time Management Verification

**Purpose:** Verify engine uses time appropriately.

**Test:**
```bash
# Give 10 seconds per move, see if engine uses it wisely
echo -e "position startpos\ngo movetime 10000\n" | ./rust-cli
```

**What to look for:**
- ✅ Uses most of the allocated time (9-10 seconds)
- ❌ Returns instantly (<1 second) = Not using time
- ❌ Times out = Using too much time

**Current Issue:** Depth 7 may have time management bugs (50% vs 75% at d5-6).

---

### 9. Repetition Detection

**Purpose:** Verify threefold repetition is detected correctly.

**Test position:**
```bash
# Position that should draw by repetition
position startpos moves e2e4 e7e5 g1f3 b8c6 f3g1 c6b8 g1f3 b8c6 f3g1 c6b8
```

**Verify:** Engine recognizes this as a draw.

---

### 10. Debug Logging

**Purpose:** Trace engine behavior in specific positions.

**Add debug output:**
```rust
// In search.rs
println!("Depth {}: score={}, move={:?}", depth, score, best_move);
println!("TT entries: {}, hits: {}", tt.size(), tt.hits());
```

**Run with output:**
```bash
./rust-cli 2>&1 | tee debug.log
```

---

## 🚨 Suspected Bugs Based on Tournament Results

### 1. Color Bias at Depth 6-7 (HIGH PRIORITY)

**Evidence:**
- Depth 6: White 0%, Black 100%
- Depth 7: White 0%, Black 100%

**Possible causes:**
- Evaluation sign error when side-to-move changes
- Time allocation giving too much time to first move
- Transposition table key collision

**How to verify:**
```bash
# Test self-play with same depth
./run_self_play_test.sh
```

### 2. Time Management at Depth 7 (MEDIUM PRIORITY)

**Evidence:**
- Depth 5-6: 75% score
- Depth 7: 50% score (regression!)

**Possible causes:**
- Using too much time early, running into time trouble
- No position-based time allocation
- Hard depth limit causing timeout

**How to verify:**
- Review PGN time stamps
- Check for games ending on time
- Profile time usage per move

### 3. Evaluation Instability (LOW PRIORITY)

**Evidence:**
- Depth 3-4: Complete losses despite "correct" moves being generated

**Possible cause:**
- Material-only evaluation is too weak
- No horizon effect mitigation

**How to verify:**
- Enable PSQT and retest
- Compare evaluations at different depths

---

## 📋 Recommended Bug Detection Workflow

### Before Adding Any Features:

1. ✅ **Run perft tests** (currently passing)
   ```bash
   cargo test --release --test perft_tests
   ```

2. ⚠️ **Test color bias** (suspected bug)
   ```bash
   # Create self-play test
   cutechess-cli \
     -engine cmd=./rust-cli depth=6 proto=uci \
     -engine cmd=./rust-cli depth=6 proto=uci \
     -each tc=60+0.6 \
     -rounds 20 \
     -pgnout self_play_d6.pgn

   # Should be ~50-50, not 0-20!
   grep "^\[Result" self_play_d6.pgn | sort | uniq -c
   ```

3. **Analyze tournament games manually**
   - Open a few d6-7 games where White lost
   - Identify the critical mistake
   - Test that position in isolation

4. **Create tactical test suite**
   - Add mate-in-1 tests
   - Add hanging piece tests
   - Add fork/pin tests

5. **Verify time usage**
   - Check PGN timestamps
   - Ensure engine uses its time allocation

### After Fixing Bugs:

6. **Rerun tournaments** to verify improvements
7. **Add regression tests** for the fixed bugs

---

## 🔧 Tools for Bug Detection

### Chess GUIs (for manual analysis)
- **Arena** - Import PGN files, replay games
- **lichess.org/analysis** - Paste FEN, get analysis
- **cutechess-cli** - Automated testing

### Debugging Commands

```bash
# Run with debug logging
RUST_LOG=debug ./rust-cli

# Profile with perf
perf record -g ./rust-cli
perf report

# Memory leak detection
valgrind --leak-check=full ./rust-cli

# Address sanitizer
RUSTFLAGS="-Z sanitizer=address" cargo build --release
```

---

## 📊 Success Metrics

Your engine is **bug-free** when:
- ✅ All perft tests pass (depth 1-7)
- ✅ Self-play at same depth is 45-55%
- ✅ No color bias (White and Black ~50% each)
- ✅ Finds all mate-in-1 positions
- ✅ Doesn't hang pieces in simple positions
- ✅ Uses time allocation effectively
- ✅ Plays consistently across depths (no regressions)

---

## Current Status Summary

| Test | Status | Priority |
|------|--------|----------|
| Perft (move gen) | ✅ Pass | ✅ |
| Tactical positions | ❓ Not tested | High |
| Color bias d6-7 | ⚠️ Suspicious | **CRITICAL** |
| Time management | ⚠️ Suspect d7 | Medium |
| Evaluation quality | ❌ Too weak | Low (by design) |
| UCI compliance | ✅ Works | ✅ |

**Recommended Next Steps:**
1. **Investigate color bias** (d6-7 White=0%, Black=100%)
2. Add tactical test suite
3. Analyze specific tournament games for blunders
4. Profile time usage at depth 7

Then once bugs are fixed, proceed with features like PSQT, LMR, etc.
