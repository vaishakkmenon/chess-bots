use rust_engine::board::Board;
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::search::eval::static_eval;
use std::str::FromStr;

fn main() {
    let tables = load_magic_tables();

    let test_fens = vec![
        (
            "Starting",
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        ),
        (
            "After e4",
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        ),
        (
            "After d4",
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",
        ),
        (
            "After a3",
            "rnbqkbnr/pppppppp/8/8/8/P7/1PPPPPPP/RNBQKBNR b KQkq - 0 1",
        ),
        (
            "After Nf3",
            "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1",
        ),
        (
            "After Nc3",
            "rnbqkbnr/pppppppp/8/8/8/2N5/PPPPPPPP/R1BQKBNR b KQkq - 1 1",
        ),
    ];

    println!("=== Static Evaluation Comparison ===\n");

    for (name, fen) in test_fens {
        let board = Board::from_str(fen).expect("Invalid FEN");
        let score = static_eval(&board, &tables);

        println!("{:12} : {:>6} centipawns", name, score);
    }

    println!("\n=== Analysis ===");
    println!("Good eval: e4/d4 should score higher than a3");
    println!("Bad eval:  All moves score the same (likely only material count)");
}
