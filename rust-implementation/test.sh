#!/bin/bash
cd /workspace/rust-implementation/rust-cli

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <version_number> <folder_name>"
    echo "Example: $0 12 v12_LMP"
    exit 1
fi

VERSION=$1
FOLDER_NAME=$2

# Build the engine (rust-cli)
cd /workspace/rust-implementation/rust-cli
cargo build --release

# Build the search benchmark tool (rust-engine)
cd /workspace/rust-implementation/rust-engine
cargo build --release --bin search_bench --features "load-magic deterministic_zobrist"

# Output directory
OUTPUT_DIR="/workspace/rust-implementation/data/benchmarks/${FOLDER_NAME}"
mkdir -p "$OUTPUT_DIR"

ENGINE_PATH="/workspace/rust-implementation/rust-cli/target/release/rust-cli"
SEARCH_BENCH_PATH="/workspace/rust-implementation/rust-engine/target/release/search_bench"

# Search Benchmarks (Depths 9-15)
SEARCH_BENCH_OUTPUT="${OUTPUT_DIR}/search_bench_results.txt"
echo "Running Search Benchmarks (Depths 9-15)..."
echo "Results will be saved to: $SEARCH_BENCH_OUTPUT"
echo "=========================================" > "$SEARCH_BENCH_OUTPUT"
echo "Search Benchmarks for Wayfinder v${VERSION}" >> "$SEARCH_BENCH_OUTPUT"
echo "Date: $(date)" >> "$SEARCH_BENCH_OUTPUT"
echo "=========================================" >> "$SEARCH_BENCH_OUTPUT"

for depth in 14 15 16 17 18 19 20; do
  echo "Running search_bench depth $depth..."
  "$SEARCH_BENCH_PATH" $depth >> "$SEARCH_BENCH_OUTPUT" 2>&1
  echo "" >> "$SEARCH_BENCH_OUTPUT"
  echo "-----------------------------------------" >> "$SEARCH_BENCH_OUTPUT"
done

# Run tournaments for depths 3-12
for depth in 3 4 5 6 7 8 9 10 11 12; do
  echo "========================================="
  echo "Running tournament: Stockfish d3 vs Wayfinder ID d${depth}"
  echo "========================================="

  cutechess-cli \
    -engine name="Stockfish" cmd=stockfish proto=uci depth=3 \
    -engine name="Wayfinder_v${VERSION}" cmd="$ENGINE_PATH" proto=uci depth=$depth \
    -each tc=60+0.6 \
    -rounds 2 \
    -repeat \
    -concurrency 1 \
    -pgnout "${OUTPUT_DIR}/stockfish_d3_vs_wayfinder_id_d${depth}.pgn" \
    -recover

  echo "Completed depth $depth"
  echo ""
done

# Compile all games into one file
COMPILED_PGN="${OUTPUT_DIR}/all_games.pgn"
echo "Compiling games into $COMPILED_PGN..."

for depth in 3 4 5 6 7 8 9 10 11 12; do
  PGN_FILE="${OUTPUT_DIR}/stockfish_d3_vs_wayfinder_id_d${depth}.pgn"
  if [ -f "$PGN_FILE" ]; then
    echo "=========================================" >> "$COMPILED_PGN"
    echo "Match: Stockfish d3 vs Wayfinder v${VERSION} ID d${depth}" >> "$COMPILED_PGN"
    echo "=========================================" >> "$COMPILED_PGN"
    cat "$PGN_FILE" >> "$COMPILED_PGN"
    echo "" >> "$COMPILED_PGN"
    echo "" >> "$COMPILED_PGN"
  fi
done

echo "========================================="
echo "All tournaments and benchmarks completed!"
echo "Results saved to: $OUTPUT_DIR"
echo "========================================="