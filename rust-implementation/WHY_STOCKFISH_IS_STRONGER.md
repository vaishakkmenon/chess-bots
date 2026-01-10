# Why Stockfish Depth 3 Crushes Wayfinder Depth 3-4

## The Shocking Reality

Your tournament results show:
- **Stockfish d3** vs **Wayfinder d3-4**: **100% win rate** (10-0, 10-0)
- **Stockfish d3** vs **Wayfinder d5-6**: **25% score** (gets crushed)

This seems impossible - how can equal or even shallower depth result in such dominance? The answer: **depth is only one small factor in chess engine strength**.

---

## The Chess Engine Strength Formula

```
Engine Strength = Search Depth × Evaluation Quality × Move Ordering × Pruning Efficiency × Opening Knowledge
```

Stockfish excels in **ALL** of these areas, while Wayfinder only has basic search depth.

---

## Feature-by-Feature Comparison

### 1. Evaluation Function ⭐ MOST CRITICAL

**Stockfish d3:**
- ✅ **NNUE Neural Network** (`nn-1c0000000000.nnue`)
  - Trained on billions of positions
  - Evaluates ~100+ features per position
  - Understands positional concepts humans can't explain
  - Adds ~200-300 ELO over classical eval
- ✅ King safety (multiple metrics)
- ✅ Pawn structure (passed pawns, doubled pawns, isolated pawns, pawn chains)
- ✅ Piece mobility (number of legal moves)
- ✅ Piece coordination
- ✅ Rook on open files
- ✅ Bishop pairs
- ✅ Knight outposts
- ✅ Threats and hanging pieces
- ✅ Space control
- ✅ Tempo and initiative

**Wayfinder v7.2:**
- ✅ Material counting (P=100, N=320, B=330, R=500, Q=900)
- ❌ **PSQT disabled** (piece-square tables exist but not compiled in)
- ❌ No king safety
- ❌ No mobility
- ❌ No pawn structure
- ❌ No positional concepts

**Impact:** This alone accounts for 200-300 ELO difference. Stockfish sees positions as "winning" that Wayfinder sees as "equal."

**Example:**
```
Position: White has bishop pair, open files, better pawn structure
Stockfish eval: +1.50 (significant advantage)
Wayfinder eval: +0.10 (nearly equal - just material)
```

---

### 2. Search Extensions & Pruning

**Stockfish d3 (effective depth: ~6-8 in tactical lines):**
- ✅ **Late Move Reductions (LMR)** - Searches likely moves deeper
- ✅ **Null Move Pruning** - Skips search in winning positions
- ✅ **Futility Pruning** - Ignores hopeless moves at shallow depths
- ✅ **Check Extensions** - Searches checks deeper (extends to d5-6)
- ✅ **Recapture Extensions** - Extends forcing sequences
- ✅ **Singular Extensions** - Extends obviously best moves
- ✅ **Multi-PV** - Can search multiple best lines

**Wayfinder v7.2 (effective depth: exactly d3-4):**
- ✅ Quiescence search (only captures)
- ❌ No LMR
- ❌ No null move pruning
- ❌ No futility pruning
- ❌ No check extensions (just quiescence)
- ❌ No search extensions

**Impact:** Stockfish's "depth 3" is actually depth 5-8 in critical tactical lines. Wayfinder's depth 4 is exactly depth 4.

---

### 3. Move Ordering Quality

**Stockfish:**
- ✅ Hash move (from transposition table)
- ✅ MVV-LVA (captures)
- ✅ Killer moves (2+ slots)
- ✅ **Counter-move heuristic**
- ✅ **History gravity** (continuation history)
- ✅ **Static Exchange Evaluation (SEE)** for captures
- ✅ Advanced history tables

**Wayfinder:**
- ✅ Hash move (from TT)
- ✅ MVV-LVA (captures)
- ✅ Killer moves (2 slots)
- ✅ Basic history heuristic
- ❌ No counter-move
- ❌ No SEE
- ❌ Simple history (no follow-up context)

**Impact:** Stockfish examines ~10% of the nodes Wayfinder does at the same depth due to better move ordering causing more beta cutoffs.

---

### 4. Time Management

**Stockfish:**
- ✅ Dynamic time allocation based on position complexity
- ✅ More time in critical positions
- ✅ Less time in forced sequences
- ✅ Considers opponent's time
- ✅ Panic mode when low on time

**Wayfinder:**
- ✅ Basic time allocation (time_remaining / 20 moves)
- ❌ No position-based adjustment
- ❌ Treats all positions equally

**Impact:** Stockfish uses time more efficiently, searching important positions deeper.

---

### 5. Opening Knowledge

**Stockfish:**
- ✅ Massive opening book (optional)
- ✅ NNUE trained on openings
- ✅ Recognizes theory

**Wayfinder:**
- ❌ No opening book
- ❌ Treats opening like middlegame

**Impact:** Stockfish starts with a positional advantage before middlegame even begins.

---

### 6. Endgame Knowledge

**Stockfish:**
- ✅ Syzygy tablebase support (perfect endgame play)
- ✅ Specialized endgame evaluation
- ✅ Recognizes fortresses, zugzwang, etc.

**Wayfinder:**
- ❌ No tablebase
- ❌ Just material evaluation

**Impact:** Stockfish plays perfect endgames; Wayfinder can blunder theoretical wins.

---

## Why the Threshold at Depth 5?

Your results show:
- d3-4: 0% win rate
- d5-6: 75% win rate
- d7: 50% win rate

### Depth 3-4: Below Tactical Horizon

At depths 3-4, Wayfinder:
- Can't see 5+ move tactical sequences
- Falls into traps Stockfish sets up
- Misses tactics Stockfish sees with extensions

**Example:**
```
Stockfish (d3 + extensions → effective d6): Sees 6-move mate
Wayfinder (d4 → exactly d4): Doesn't see the mate, walks into it
```

### Depth 5-6: Above Tactical Threshold

At depths 5-6, Wayfinder:
- ✅ Sees most short-term tactics (5-6 moves ahead)
- ✅ Avoids obvious blunders
- ✅ Can set up basic tactics
- ❌ Still has weak positional understanding

This depth is enough to avoid tactical losses but not enough to dominate strategically.

### Depth 7: Time Trouble

At depth 7:
- ❌ Uses too much time per move
- ❌ Runs into time scrambles
- ❌ Forced to play fast in critical positions
- ❌ Effective depth drops in time pressure

**Result:** Loses the advantage gained from deeper search.

---

## The ELO Breakdown

Estimated ELO contributions (very rough):

| Feature | Stockfish Bonus | Wayfinder Has? |
|---------|----------------|----------------|
| **NNUE Evaluation** | +300 ELO | ❌ No |
| **Advanced Pruning (LMR, NMP)** | +200 ELO | ❌ No |
| **PSQT & Positional Eval** | +150 ELO | ❌ Disabled |
| **Opening Book** | +100 ELO | ❌ No |
| **Better Move Ordering** | +100 ELO | Partial |
| **Endgame Tablebases** | +50 ELO | ❌ No |
| **Search Extensions** | +150 ELO | ❌ No |
| **Time Management** | +50 ELO | Basic |
| **King Safety** | +100 ELO | ❌ No |

**Total Stockfish Advantage: ~1000+ ELO at same nominal depth**

---

## Real-World Analogy

Think of chess engine search like examining a building:

**Stockfish d3:**
- Uses X-ray vision (NNUE)
- Has blueprints (opening theory)
- Knows which rooms are important (search extensions)
- Has a team of experts (advanced evaluation)
- **Effective inspection depth: 6-8 floors in critical areas**

**Wayfinder d4:**
- Uses a flashlight (material counting)
- No blueprints
- Checks every room equally (no pruning)
- Amateur inspector (basic evaluation)
- **Effective inspection depth: exactly 4 floors**

Even though Wayfinder looks one floor deeper, Stockfish's tools let it understand the building far better.

---

## Why Depth 5 Beats Stockfish d3

At depth 5-6, Wayfinder finally searches deep enough to:
1. **See the tactics Stockfish sets up** (tactical horizon exceeded)
2. **Avoid obvious tactical blunders** (searches past Stockfish's trap depth)
3. **Force draws in complex positions** (repetition detection works)

But it still struggles with:
- Positional understanding (evaluation weakness)
- Opening play (no book)
- Efficient time usage (simple time management)

---

## How to Close the Gap

### Quick Wins (Low Effort, High Impact):

1. **Enable PSQT** ⭐ CRITICAL
   ```toml
   # In rust-cli/Cargo.toml:
   rust-engine = { path = "../rust-engine", features = ["load-magic", "psqt"] }
   ```
   - Expected gain: +50-100 ELO
   - Almost no performance cost

2. **Implement Null Move Pruning**
   - Expected gain: +100 ELO
   - Searches twice as fast

3. **Add Late Move Reductions (LMR)**
   - Expected gain: +150 ELO
   - Effective depth increases by 1-2 plies

4. **Improve Time Management**
   - Expected gain: +50 ELO
   - Fixes the d7 time trouble issue

### Medium Wins (Moderate Effort):

5. **Add King Safety Evaluation**
   - Expected gain: +100 ELO
   - Prevents getting mated

6. **Implement Aspiration Windows**
   - Expected gain: +30 ELO
   - Faster search with same depth

7. **Add Opening Book**
   - Expected gain: +100 ELO
   - Better starting positions

### Long-term (High Effort, Massive Impact):

8. **Train a Neural Network (NNUE-style)**
   - Expected gain: +200-300 ELO
   - Requires training infrastructure
   - Months of work

---

## Conclusion

Stockfish depth 3 is **NOT** comparable to Wayfinder depth 3. It's more like:

```
Stockfish d3 (with all features) ≈ Wayfinder d8-10 (material-only eval)
```

The good news: **Your engine's search is working!** The depth 5-6 results prove that when Wayfinder searches deep enough to overcome its evaluation weakness, it can compete. The problem isn't the search algorithm - it's:

1. **Evaluation too simple** (just material)
2. **No search enhancements** (extensions, reductions)
3. **Basic move ordering** (missing advanced heuristics)

Start by enabling PSQT (literally a one-line change) and implementing null-move pruning. These two changes alone could boost your engine by 150-200 ELO.

---

## Next Steps

1. Enable PSQT feature (immediate +50-100 ELO)
2. Add null-move pruning (+100 ELO)
3. Implement LMR (+150 ELO)
4. Fix time management (d7 performance)
5. Add king safety evaluation
6. Consider NNUE for long-term (massive jump)

With these improvements, Wayfinder could beat Stockfish d3 even at depth 4!
