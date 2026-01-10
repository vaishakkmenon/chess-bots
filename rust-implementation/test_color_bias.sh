#!/bin/bash

# Test for color bias by having Wayfinder play against itself
# Should result in approximately 50-50 split

cd /workspace/rust-implementation/rust-cli

echo "========================================="
echo "Color Bias Test: Wayfinder vs Itself"
echo "========================================="
echo ""
echo "This test verifies that the engine doesn't have a color bias."
echo "Results should be approximately 50% for each color."
echo ""

# Build the engine
echo "Building engine..."
cargo build --release --quiet

OUTPUT_DIR="/workspace/rust-implementation/rust-engine/src/search/results/color_bias_test"
mkdir -p "$OUTPUT_DIR"

ENGINE_PATH="/workspace/rust-implementation/rust-cli/target/release/rust-cli"

# Test depth 6 (where color bias was observed)
echo "========================================="
echo "Testing Depth 6 (10 games = 20 with reversed colors)"
echo "========================================="

cutechess-cli \
  -engine name="Wayfinder_A" cmd="$ENGINE_PATH" proto=uci depth=6 \
  -engine name="Wayfinder_B" cmd="$ENGINE_PATH" proto=uci depth=6 \
  -each tc=60+0.6 \
  -rounds 10 \
  -repeat \
  -concurrency 1 \
  -pgnout "${OUTPUT_DIR}/self_play_d6.pgn" \
  -recover

echo ""
echo "========================================="
echo "Results Analysis"
echo "========================================="

# Count results
WHITE_WINS=$(grep -c '^\[Result "1-0"\]' "${OUTPUT_DIR}/self_play_d6.pgn")
BLACK_WINS=$(grep -c '^\[Result "0-1"\]' "${OUTPUT_DIR}/self_play_d6.pgn")
DRAWS=$(grep -c '^\[Result "1/2-1/2"\]' "${OUTPUT_DIR}/self_play_d6.pgn")

echo "White wins: $WHITE_WINS"
echo "Black wins: $BLACK_WINS"
echo "Draws: $DRAWS"
echo ""

# Calculate percentages
TOTAL=$((WHITE_WINS + BLACK_WINS + DRAWS))
if [ $TOTAL -gt 0 ]; then
  WHITE_PCT=$(echo "scale=1; $WHITE_WINS * 100 / $TOTAL" | bc)
  BLACK_PCT=$(echo "scale=1; $BLACK_WINS * 100 / $TOTAL" | bc)
  DRAW_PCT=$(echo "scale=1; $DRAWS * 100 / $TOTAL" | bc)

  echo "White: ${WHITE_PCT}%"
  echo "Black: ${BLACK_PCT}%"
  echo "Draws: ${DRAW_PCT}%"
  echo ""
fi

# Diagnosis
echo "========================================="
echo "Diagnosis"
echo "========================================="

if [ $WHITE_WINS -eq 0 ] && [ $BLACK_WINS -gt 15 ]; then
  echo "❌ CRITICAL BUG: Severe color bias detected!"
  echo "   Engine never wins as White against itself."
  echo "   This indicates a bug in:"
  echo "   - Evaluation sign (returning wrong perspective)"
  echo "   - Time management (using all time on first moves)"
  echo "   - Or transposition table key generation"
elif [ $BLACK_WINS -eq 0 ] && [ $WHITE_WINS -gt 15 ]; then
  echo "❌ CRITICAL BUG: Severe color bias detected!"
  echo "   Engine never wins as Black against itself."
elif [ ${WHITE_WINS#0} -ge 8 ] && [ ${WHITE_WINS#0} -le 12 ] && [ ${BLACK_WINS#0} -ge 8 ] && [ ${BLACK_WINS#0} -le 12 ]; then
  echo "✅ HEALTHY: No significant color bias detected."
  echo "   Results are within expected range (40-60%)."
elif [ $((WHITE_WINS + BLACK_WINS)) -eq 0 ]; then
  echo "⚠️  All games drawn. This is unusual but not necessarily a bug."
else
  echo "⚠️  Moderate color bias detected."
  echo "   Consider investigating, but may be within variance."
fi

echo ""
echo "PGN file saved to: ${OUTPUT_DIR}/self_play_d6.pgn"
echo "========================================="
