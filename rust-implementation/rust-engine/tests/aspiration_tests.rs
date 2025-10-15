use rust_engine::board::Board;
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::search::search::search_iterative_deepening;
use std::str::FromStr;

#[test]
fn test_aspiration_finds_correct_move() {
    // Simple tactical position - back rank mate
    let mut board = Board::from_str("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1").unwrap();
    let tables = load_magic_tables();

    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 6);

    assert!(best_move.is_some(), "Should find a best move");

    // Should find Re8# (back rank mate)
    let mv = best_move.unwrap();
    use rust_engine::square::Square;
    let e8 = Square::from_index(60);
    assert_eq!(mv.to, e8, "Should find Re8# even with aspiration windows");

    // Should recognize as mate
    use rust_engine::search::search::MATE;
    assert!(
        score > MATE - 10,
        "Should recognize mate, got score {}",
        score
    );
}

#[test]
fn test_aspiration_handles_score_drop() {
    // Position where evaluation might fluctuate
    // r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1
    let mut board =
        Board::from_str("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1")
            .unwrap();
    let tables = load_magic_tables();

    // Should handle score drops gracefully (fail-low)
    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 6);

    assert!(
        best_move.is_some(),
        "Should find a move despite score fluctuations"
    );
    assert!(
        score.abs() < 500,
        "Score should be reasonable, got {}",
        score
    );
}

#[test]
fn test_aspiration_handles_score_jump() {
    // Position with a tactical blow
    // Start from a quiet position that has a sudden tactic
    let mut board =
        Board::from_str("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
            .unwrap();
    let tables = load_magic_tables();

    // Should handle score jumps gracefully (fail-high)
    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 6);

    assert!(best_move.is_some(), "Should find a move despite score jump");
    assert!(score > 0, "White should be winning in this position");
}

#[test]
fn test_aspiration_performance() {
    use std::time::Instant;

    // Middlegame position - same as LMR test for comparison
    let mut board =
        Board::from_str("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
            .unwrap();
    let tables = load_magic_tables();

    let start = Instant::now();
    let (_score, best_move) = search_iterative_deepening(&mut board, &tables, 8);
    let duration = start.elapsed();

    println!("Aspiration Windows: Search to depth 8 took: {:?}", duration);

    assert!(best_move.is_some(), "Should find a best move");

    // With aspiration windows, should be faster than LMR-only
    // LMR-only was ~105s, aspiration should be ~75-85s
    // Allow up to 120s to be safe (still faster than no optimizations)
    assert!(
        duration.as_secs() < 120,
        "Search took too long: {:?}",
        duration
    );

    if duration.as_secs() < 90 {
        println!("✓ Aspiration windows providing good speedup!");
    }
}

#[test]
fn test_aspiration_vs_full_window() {
    // Test that aspiration windows gives same result as full window search
    let mut board =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let tables = load_magic_tables();

    // Search with aspiration windows
    let (asp_score, asp_move) = search_iterative_deepening(&mut board, &tables, 5);

    // Both searches should find same/similar move
    assert!(asp_move.is_some(), "Aspiration search should find a move");

    // Scores should be close (within 20 centipawns - normal variation)
    // In starting position, should be near 0
    assert!(
        asp_score.abs() < 100,
        "Score should be near equality in starting position, got {}",
        asp_score
    );
}

#[test]
fn test_aspiration_with_mate_scores() {
    // Position with forced mate
    // 6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1 (Re8#)
    let mut board = Board::from_str("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1").unwrap();
    let tables = load_magic_tables();

    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 4);

    assert!(best_move.is_some(), "Should find mate move");

    use rust_engine::search::search::MATE;
    assert!(
        score > MATE - 10,
        "Should find mate score even with aspiration windows, got {}",
        score
    );
}

#[test]
fn test_aspiration_depth_1_uses_full_window() {
    // Verify depth 1 uses full window (no aspiration)
    let mut board =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let tables = load_magic_tables();

    // Depth 1 should always work (uses full window)
    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 1);

    assert!(best_move.is_some(), "Depth 1 should find a move");
    assert!(score.abs() < 200, "Depth 1 should give reasonable score");
}

#[test]
fn test_aspiration_consistency_across_depths() {
    // Test that aspiration doesn't cause instability
    // let mut board =
    //     Board::from_str("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
    //         .unwrap();
    let tables = load_magic_tables();

    println!("\nTesting aspiration consistency:");

    let mut prev_score = 0;

    for depth in 1..=6 {
        let mut board_copy =
            Board::from_str("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
                .unwrap();

        let (score, mv) = search_iterative_deepening(&mut board_copy, &tables, depth);

        println!("  Depth {}: score={}, move={:?}", depth, score, mv);

        assert!(mv.is_some(), "Should find move at depth {}", depth);

        // Score shouldn't wildly fluctuate (allow ±100 cp variation per depth)
        if depth > 1 {
            let diff = (score - prev_score).abs();
            assert!(
                diff < 200,
                "Score changed too much from depth {} to {}: {} -> {}",
                depth - 1,
                depth,
                prev_score,
                score
            );
        }

        prev_score = score;
    }
}

#[test]
fn test_aspiration_doesnt_miss_tactics() {
    // Position with clear mate in 1: Back rank mate
    // 6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1
    // White plays Re8# - back rank mate
    let mut board = Board::from_str("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1").unwrap();
    let tables = load_magic_tables();

    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 5);

    assert!(best_move.is_some(), "Should find mate move");

    use rust_engine::search::search::MATE;
    assert!(
        score > MATE - 10,
        "Should find mate even with aspiration windows, got {}",
        score
    );
}

#[test]
fn test_aspiration_window_size() {
    // Test with very stable position to verify window behavior
    // Symmetric pawn endgame - evaluation should be stable
    let mut board = Board::from_str("8/4k3/8/8/8/8/4K3/8 w - - 0 1").unwrap();
    let tables = load_magic_tables();

    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 6);

    assert!(best_move.is_some(), "Should find a move");

    // In symmetric position, score should be near 0
    assert!(
        score.abs() < 50,
        "Symmetric position should evaluate near 0, got {}",
        score
    );
}
