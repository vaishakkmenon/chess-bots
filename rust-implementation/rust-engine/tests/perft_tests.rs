#[cfg(test)]
mod tests {
    use rust_engine::board::Board;
    use rust_engine::logger::init_logging;
    use rust_engine::moves::magic::{MagicTableSeed, generate_magic_tables};
    use rust_engine::moves::perft::{perft, perft_divide};

    const START_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    const KIWI_FEN: &str = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";

    #[test]
    fn perft_startpos_depths() {
        let tables = generate_magic_tables(MagicTableSeed::Fixed(69)).expect("magic tables");

        // Known node counts for startpos
        let expected = [
            (1, 20u64),
            (2, 400),
            (3, 8902),
            (4, 197_281),
            (5, 4_865_609), // uncomment when it’s fast enough
        ];

        for (depth, expected_nodes) in expected {
            let mut board = Board::new(); // start with default state
            board.set_fen(START_FEN).expect("valid startpos");
            let nodes = perft(&mut board, &tables, depth);
            println!("Depth: {}, Nodes: {}", depth, nodes);
            assert_eq!(
                nodes, expected_nodes,
                "Perft mismatch at depth {}: got {}, expected {}",
                depth, nodes, expected_nodes
            );
        }
    }

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

    /// Kiwipete known perft counts:
    /// d1 = 48
    /// d2 = 2,039
    /// d3 = 97,862
    /// d4 = 4,085,603
    /// d5 = 193,690,690  (heavy; usually skipped unless highly optimized)
    #[test]
    fn perft_kiwipete_complete() {
        let tables = generate_magic_tables(MagicTableSeed::Fixed(69)).expect("magic tables");

        let expected = [
            (1, 48u64),
            (2, 2_039),
            (3, 97_862),
            (4, 4_085_603),
            // (5, 193_690_690), // uncomment when fast enough
        ];

        for (depth, expected_nodes) in expected {
            let mut board = Board::new();
            board.set_fen(KIWI_FEN).expect("valid kiwipete");
            let nodes = perft(&mut board, &tables, depth);
            println!("[Kiwipete] Depth: {depth}, Nodes: {nodes}");
            assert_eq!(
                nodes, expected_nodes,
                "[Kiwipete] Perft mismatch at depth {depth}: got {nodes}, expected {expected_nodes}"
            );
        }
    }

    #[test]
    fn perft_kiwipete_divide() {
        let tables = generate_magic_tables(MagicTableSeed::Fixed(69)).unwrap();
        let mut board = Board::new();
        board.set_fen(KIWI_FEN).unwrap();
        perft_divide(&mut board, &tables, 2);
    }

    #[test]
    fn kiwipete_d2_tally() {
        use rust_engine::board::Board;
        use rust_engine::moves::execute::generate_legal;
        use rust_engine::moves::magic::{MagicTableSeed, generate_magic_tables};
        use std::str::FromStr;

        let mut b = Board::from_str(KIWI_FEN).unwrap();
        let t = generate_magic_tables(MagicTableSeed::Fixed(69)).unwrap();

        let mut roots = vec![];
        generate_legal(&mut b, &t, &mut roots);

        let mut nodes = 0u64;
        let mut captures = 0u64;
        let mut ep = 0u64;
        let mut castles = 0u64;
        let mut checks = 0u64;

        for mv in roots {
            let u = rust_engine::moves::execute::make_move_basic(&mut b, mv);
            // depth-2: enumerate Black replies
            let mut replies = vec![];
            generate_legal(&mut b, &t, &mut replies);

            nodes += replies.len() as u64;
            for r in &replies {
                if r.is_capture {
                    captures += 1;
                }
                if r.is_en_passant {
                    ep += 1;
                }
                if r.is_castling {
                    castles += 1;
                }
                // quick check detector
                let uu = rust_engine::moves::execute::make_move_basic(&mut b, *r);
                let in_chk = rust_engine::moves::square_control::in_check(&b, b.side_to_move, &t);
                if in_chk {
                    checks += 1;
                }
                rust_engine::moves::execute::undo_move_basic(&mut b, uu);
            }

            rust_engine::moves::execute::undo_move_basic(&mut b, u);
        }

        println!("d2 nodes={nodes} captures={captures} ep={ep} castles={castles} checks={checks}");
        assert_eq!(nodes, 2039);
        assert_eq!(captures, 351);
        assert_eq!(ep, 1);
        assert_eq!(castles, 91);
        assert_eq!(checks, 3);
    }
}
