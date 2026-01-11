#!/bin/bash
cd /workspace/rust-implementation/rust-cli

# Build the engine (rust-cli doesn't need features, they're passed to rust-engine via Cargo.toml)
cargo build --release

# Output directory
OUTPUT_DIR="/workspace/rust-implementation/data/benchmarks/v9_Mop_Up"
mkdir -p "$OUTPUT_DIR"

ENGINE_PATH="/workspace/rust-implementation/rust-cli/target/release/rust-cli"

# Run tournaments for depths 3-7
for depth in 3 4 5 6 7; do
  echo "========================================="
  echo "Running tournament: Stockfish d3 vs Wayfinder ID d${depth}"
  echo "========================================="

  cutechess-cli \
    -engine name="Stockfish" cmd=stockfish proto=uci depth=3 \
    -engine name="Wayfinder_v8" cmd="$ENGINE_PATH" proto=uci depth=$depth \
    -each tc=60+0.6 \
    -rounds 2 \
    -repeat \
    -concurrency 1 \
    -pgnout "${OUTPUT_DIR}/stockfish_d3_vs_wayfinder_id_d${depth}.pgn" \
    -recover

  echo "Completed depth $depth"
  echo ""
done

echo "========================================="
echo "All tournaments completed!"
echo "Results saved to: $OUTPUT_DIR"
echo "========================================="