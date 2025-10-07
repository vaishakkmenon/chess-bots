use rust_engine::board::Board;
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::moves::perft::perft;
use std::env;
use std::time::Instant;

fn main() {
    let args: Vec<String> = env::args().collect();
    let depth: u32 = if args.len() > 1 {
        args[1].parse().expect("Invalid depth argument")
    } else {
        5
    };

    println!("Running perft benchmark at depth {}", depth);

    let tables = load_magic_tables();
    let mut board = Board::new();

    let start = Instant::now();
    let nodes = perft(&mut board, &tables, depth);
    let elapsed = start.elapsed();

    let secs = elapsed.as_secs_f64();
    let nps = (nodes as f64 / secs) as u64;

    println!("\nResults:");
    println!("  Depth: {}", depth);
    println!("  Nodes: {}", nodes);
    println!("  Time:  {:.3}s", secs);
    println!("  NPS:   {} nodes/sec", nps);
}
