#[cfg(test)]
mod tests {
    use rust_engine::board::Board;
    use rust_engine::logger::init_logging;
    use rust_engine::moves::magic::{MagicTableSeed, generate_magic_tables};
    use rust_engine::moves::perft::{perft, perft_divide};

    const START_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    // #[test]
    // fn perft_startpos_depths() {
    //     let tables = generate_magic_tables(MagicTableSeed::Fixed(69)).expect("magic tables");

    //     // Known node counts for startpos
    //     let expected = [
    //         (1, 20u64),
    //         (2, 400),
    //         (3, 8902),
    //         (4, 197_281),
    //         // (5, 4_865_609), // uncomment when it’s fast enough
    //     ];

    //     for (depth, expected_nodes) in expected {
    //         let mut board = Board::new(); // start with default state
    //         board.set_fen(START_FEN).expect("valid startpos");
    //         let nodes = perft(&mut board, &tables, depth);
    //         assert_eq!(
    //             nodes, expected_nodes,
    //             "Perft mismatch at depth {}: got {}, expected {}",
    //             depth, nodes, expected_nodes
    //         );
    //     }
    // }

    #[test]
    fn perft_debug_divide() {
        use tracing::info;
        init_logging(
            "logs/perft.log",
            "rust_engine::moves::perft=trace,rust_engine::moves::execute=debug,info",
        );
        info!("perft_divide started");
        let tables = generate_magic_tables(MagicTableSeed::Fixed(69)).unwrap();
        let mut board = Board::new();
        board.set_fen(START_FEN).unwrap();
        perft_divide(&mut board, &tables, 3);
    }
}
