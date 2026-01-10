#!/bin/bash
# Test against WEAKENED Stockfish (Skill Level 0) for more competitive games

cd /workspace/rust-implementation/rust-cli

# Build the engine
echo "Building engine..."
cargo build --release

# Output directory
OUTPUT_DIR="/workspace/rust-implementation/rust-engine/src/search/results/v7.2_weakened_stockfish"
mkdir -p "$OUTPUT_DIR"

ENGINE_PATH="/workspace/rust-implementation/rust-cli/target/release/rust-cli"

echo "========================================="
echo "Testing against WEAKENED Stockfish"
echo "Stockfish: Skill Level 0 (weakest)"
echo "This creates more competitive games"
echo "========================================="
echo ""

# Run tournaments for depths 3-7
for depth in 3 4 5 6 7; do
  echo "========================================="
  echo "Running tournament: Stockfish d3 (Skill 0) vs Wayfinder ID d${depth}"
  echo "========================================="

  cutechess-cli \
    -engine name="Stockfish_Weak" cmd=stockfish proto=uci option."Skill Level"=0 depth=3 \
    -engine name="Wayfinder_v7.2" cmd="$ENGINE_PATH" proto=uci depth=$depth \
    -each tc=60+0.6 \
    -rounds 10 \
    -repeat \
    -concurrency 1 \
    -pgnout "${OUTPUT_DIR}/stockfish_weak_d3_vs_wayfinder_id_d${depth}.pgn" \
    -recover

  echo "Completed depth $depth"
  echo ""
done

echo "========================================="
echo "All tournaments completed!"
echo "Results saved to: $OUTPUT_DIR"
echo "========================================="
