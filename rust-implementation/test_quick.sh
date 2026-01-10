#!/bin/bash
# Quick test with just 2 rounds to verify everything works

cd /workspace/rust-implementation/rust-cli

# Build the engine
echo "Building engine..."
cargo build --release

# Output directory
OUTPUT_DIR="/workspace/rust-implementation/rust-engine/src/search/results/v7.2_time_management_test"
mkdir -p "$OUTPUT_DIR"

ENGINE_PATH="/workspace/rust-implementation/rust-cli/target/release/rust-cli"

echo "========================================="
echo "Quick Test: Stockfish d3 vs Wayfinder ID d5"
echo "Running 2 rounds (4 games total)"
echo "========================================="

cutechess-cli \
  -engine name="Stockfish" cmd=stockfish proto=uci depth=3 \
  -engine name="Wayfinder_v7.2" cmd="$ENGINE_PATH" proto=uci depth=5 \
  -each tc=60+0.6 \
  -rounds 2 \
  -repeat \
  -concurrency 1 \
  -pgnout "${OUTPUT_DIR}/quick_test.pgn" \
  -recover

echo ""
echo "========================================="
echo "Quick test completed!"
echo "Results saved to: ${OUTPUT_DIR}/quick_test.pgn"
echo "========================================="

# Show results summary
if [ -f "${OUTPUT_DIR}/quick_test.pgn" ]; then
  echo ""
  echo "Game count:"
  grep -c "^\[Event" "${OUTPUT_DIR}/quick_test.pgn"
  echo ""
  echo "Results breakdown:"
  grep "^\[Result" "${OUTPUT_DIR}/quick_test.pgn"
fi
