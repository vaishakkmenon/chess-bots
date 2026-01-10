// Save this as: src/bin/eval_debug.rs
// Build with: cargo build --release --bin eval_debug --features "load-magic deterministic_zobrist psqt"
// Run with: /workspace/target/release/eval_debug
use rust_engine::board::{Board, Color, Piece};
use rust_engine::search::eval::{eval_material, eval_psqt, static_eval};
use std::str::FromStr;

fn main() {
    println!("=== Chess Engine Evaluation Debug ===\n");

    // Test 1: Starting position
    let start_board = Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        .expect("Invalid FEN");

    println!("=== Starting Position ===");
    println!("FEN: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    debug_eval(&start_board);
    println!();

    // Add this test case to eval_debug.rs
    let after_e3 = Board::from_str("rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        .expect("Invalid FEN");

    println!("=== After e2-e3 ===");
    println!("FEN: rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR b KQkq - 0 1");
    debug_eval(&after_e3);

    // Test 2: After e2-e4
    let after_e4 = Board::from_str("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        .expect("Invalid FEN");

    println!("=== After e2-e4 ===");
    println!("FEN: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1");
    debug_eval(&after_e4);
    println!();

    // Test 3: After d2-d4
    let after_d4 = Board::from_str("rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1")
        .expect("Invalid FEN");

    println!("=== After d2-d4 ===");
    println!("FEN: rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1");
    debug_eval(&after_d4);
    println!();

    // Test 4: After a2-a3
    let after_a3 = Board::from_str("rnbqkbnr/pppppppp/8/8/8/P7/1PPPPPPP/RNBQKBNR b KQkq - 0 1")
        .expect("Invalid FEN");

    println!("=== After a2-a3 ===");
    println!("FEN: rnbqkbnr/pppppppp/8/8/8/P7/1PPPPPPP/RNBQKBNR b KQkq - 0 1");
    debug_eval(&after_a3);
    println!();

    // Test 5: After Nf3
    let after_nf3 = Board::from_str("rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1")
        .expect("Invalid FEN");

    println!("=== After Nf3 ===");
    println!("FEN: rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1");
    debug_eval(&after_nf3);
}

fn debug_eval(board: &Board) {
    let material = eval_material(board);
    let psqt = eval_psqt(board);
    let total = static_eval(board);

    println!("Side to move: {:?}", board.side_to_move);
    println!("Material score (White perspective): {} cp", material);
    println!("PSQT score (White perspective):     {} cp", psqt);
    println!("Combined (White perspective):       {} cp", material + psqt);
    println!("Static eval (current player):       {} cp", total);

    // Show piece positions
    println!("\nWhite pieces:");
    debug_pieces(board, Color::White);
    println!("\nBlack pieces:");
    debug_pieces(board, Color::Black);
}

fn debug_pieces(board: &Board, color: Color) {
    for piece in [
        Piece::Pawn,
        Piece::Knight,
        Piece::Bishop,
        Piece::Rook,
        Piece::Queen,
        Piece::King,
    ] {
        let bb = board.pieces(piece, color);
        if bb.count_ones() > 0 {
            print!("  {:?}s: ", piece);
            let mut first = true;
            for sq in 0..64 {
                if bb & (1u64 << sq) != 0 {
                    if !first {
                        print!(", ");
                    }
                    print!("{}", square_name(sq));
                    first = false;
                }
            }
            println!();
        }
    }
}

fn square_name(sq: u8) -> String {
    let file = sq % 8;
    let rank = sq / 8;
    format!("{}{}", (b'a' + file) as char, rank + 1)
}
