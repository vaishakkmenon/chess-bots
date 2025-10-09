use rust_engine::board::Board;
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::search::search::search_fixed_depth;
use std::env;
use std::str::FromStr;
use std::time::Instant;

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: search_bench <depth> [fen]");
        eprintln!();
        eprintln!("Examples:");
        eprintln!("  search_bench 6");
        eprintln!("  search_bench 7 \"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\"");
        eprintln!();
        eprintln!("Tactical position to test:");
        eprintln!(
            "  search_bench 6 \"r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1\""
        );
        std::process::exit(1);
    }

    let depth: i32 = args[1].parse().expect("Depth must be a number");

    let fen = if args.len() > 2 {
        args[2].clone()
    } else {
        // Default: starting position
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1".to_string()
    };

    println!("=== Chess Engine Search Benchmark ===\n");
    println!("Loading magic tables...");
    let tables = load_magic_tables();

    println!("Position: {}", fen);
    let mut board = Board::from_str(&fen).expect("Invalid FEN");

    println!("Depth: {}", depth);
    println!("\nSearching...\n");

    let start = Instant::now();
    let (score, best_move) = search_fixed_depth(&mut board, &tables, depth);
    let elapsed = start.elapsed();

    println!("=== Results ===");
    println!("Time:      {:.3}s", elapsed.as_secs_f64());

    match best_move {
        Some(mv) => {
            println!("Best move: {:?}", mv);
            println!("Score:     {} centipawns", score);
        }
        None => {
            println!("No legal moves (checkmate or stalemate)");
            println!("Score:     {}", score);
        }
    }
}
