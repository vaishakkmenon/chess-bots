#!/bin/bash

# Diagnose the color bias by analyzing a specific game position

cd /workspace/rust-implementation/rust-cli
cargo build --release --quiet 2>&1 | grep -v "Compiling\|Finished" || true

ENGINE="./target/release/rust-cli"

echo "========================================="
echo "Color Bias Diagnostic Test"
echo "========================================="
echo ""

# Test the opening moves from the self-play game
echo "Testing opening position (move 1):"
echo "-----------------------------------"

# Position after 1.Nc3 (White just moved)
echo "Position: After 1.Nc3 (Black to move)"
echo "FEN: rnbqkbnr/pppppppp/8/8/8/2N5/PPPPPPPP/R1BQKBNR b KQkq - 1 1"
echo ""
echo "Black's evaluation:"
echo -e "position fen rnbqkbnr/pppppppp/8/8/8/2N5/PPPPPPPP/R1BQKBNR b KQkq - 1 1\ngo depth 6\nquit" | $ENGINE 2>&1 | grep "^info depth 6"
echo ""

echo "Now same position, but White to move (impossible, but tests TT):"
echo "FEN: rnbqkbnr/pppppppp/8/8/8/2N5/PPPPPPPP/R1BQKBNR w KQkq - 1 1"
echo "White's evaluation:"
echo -e "position fen rnbqkbnr/pppppppp/8/8/8/2N5/PPPPPPPP/R1BQKBNR w KQkq - 1 1\ngo depth 6\nquit" | $ENGINE 2>&1 | grep "^info depth 6"
echo ""

echo "========================================="
echo "Testing starting position:"
echo "-----------------------------------"

# Starting position - White to move
echo "Starting position (White to move):"
echo "FEN: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
echo ""
echo "White's evaluation and best move:"
echo -e "position startpos\ngo depth 6\nquit" | $ENGINE 2>&1 | grep "^info depth 6"
echo ""

# Starting position - Black to move (illegal, but tests perspective)
echo "Starting position (Black to move - illegal but tests TT):"
echo "FEN: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
echo ""
echo "Black's evaluation:"
echo -e "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1\ngo depth 6\nquit" | $ENGINE 2>&1 | grep "^info depth 6"
echo ""

echo "========================================="
echo "Testing critical position (move 21):"
echo "-----------------------------------"

# Position where evaluation flips (after move 21.Ke3)
echo "Position after 21.Ke3 (Black to move):"
echo "FEN: r7/p1p5/2p1pnpk/8/2P5/2P1K3/P5PP/R6R b - - 0 21"
echo ""
echo "Black's evaluation:"
echo -e "position fen 5rk1/p1p5/2p1pn2/8/2P3r1/2P1K3/P5PP/R6R b - - 0 21\ngo depth 6\nquit" | $ENGINE 2>&1 | grep "^info depth"
echo ""

echo "========================================="
echo "Diagnosis Complete"
echo "========================================="
echo ""
echo "EXPECTED BEHAVIOR:"
echo "- Starting position should eval to ~0.00 for both White and Black"
echo "- After 1.Nc3, Black should see slight disadvantage (-0.20 is correct)"
echo "- Scores should be properly negated for opposite colors"
echo ""
echo "IF BUGGY:"
echo "- Scores might be inverted or incorrectly signed"
echo "- TT might be returning wrong scores for different colors"
echo ""
