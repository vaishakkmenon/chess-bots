use rust_engine::board::Board;
use std::str::FromStr;

fn main() {
    let fens = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2",
        "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
    ];

    println!("Debugging FEN Parsing...");
    for (i, fen) in fens.iter().enumerate() {
        print!("FEN #{}: '{}' -> ", i + 1, fen);
        match Board::from_str(fen) {
            Ok(_) => println!("OK"),
            Err(e) => println!("ERROR: {}", e),
        }
    }
}
