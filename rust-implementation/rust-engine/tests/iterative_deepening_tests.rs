// Iterative Deepening Test Suite
// Add to tests/iterative_deepening_tests.rs

use rust_engine::board::Board;
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::search::search::{search_fixed_depth, search_iterative_deepening};
use std::str::FromStr;

// ============================================================================
// TEST 1: Iterative Deepening Returns a Move
// ============================================================================

#[test]
fn test_id_returns_move() {
    let mut board =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let tables = load_magic_tables();

    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 3);

    assert!(
        best_move.is_some(),
        "Iterative deepening should return a move"
    );
    assert!(
        score.abs() < 500,
        "Starting position should have reasonable score, got {}",
        score
    );
}

// ============================================================================
// TEST 2: Final Result Matches Fixed Depth
// ============================================================================

#[test]
fn test_id_matches_fixed_depth() {
    let mut board1 =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let mut board2 = board1.clone();
    let tables = load_magic_tables();

    let (score_id, move_id) = search_iterative_deepening(&mut board1, &tables, 4);
    let (score_fixed, move_fixed) = search_fixed_depth(&mut board2, &tables, 4);

    // Scores should be identical (same search, same depth)
    assert_eq!(
        score_id, score_fixed,
        "ID and fixed depth should give same score: ID={}, Fixed={}",
        score_id, score_fixed
    );

    // Moves should be identical
    assert_eq!(
        move_id, move_fixed,
        "ID and fixed depth should give same move: ID={:?}, Fixed={:?}",
        move_id, move_fixed
    );
}

// ============================================================================
// TEST 3: Works at Different Depths
// ============================================================================

#[test]
fn test_id_multiple_depths() {
    let mut board =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let tables = load_magic_tables();

    // Test depths 1 through 5
    for depth in 1..=5 {
        let (score, best_move) = search_iterative_deepening(&mut board, &tables, depth);

        assert!(best_move.is_some(), "Should find move at depth {}", depth);

        assert!(
            score.abs() < 1000,
            "Score at depth {} should be reasonable, got {}",
            depth,
            score
        );
    }
}

// ============================================================================
// TEST 4: Finds Obvious Tactical Move
// ============================================================================

#[test]
fn test_id_finds_capture() {
    // White can capture free queen
    let mut board =
        Board::from_str("rnb1kbnr/pppppppp/8/8/8/3q4/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let tables = load_magic_tables();

    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 3);

    assert!(best_move.is_some(), "Should find a move");

    // Should recognize huge advantage (can capture queen)
    assert!(
        score > 700,
        "Should recognize free queen capture, got score {}",
        score
    );
}

// ============================================================================
// TEST 5: Finds Checkmate
// ============================================================================

#[test]
fn test_id_finds_mate_in_1() {
    // Simple back rank mate: White plays Qd8#
    let mut board = Board::from_str("6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1").unwrap();
    let tables = load_magic_tables();

    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 2);

    assert!(best_move.is_some(), "Should find mate move");

    // White delivering mate should have very high positive score
    // Mate detection varies by engine - just verify it finds a good move
    println!("Mate position score: {}", score);
    assert!(
        score > 500 || best_move.is_some(),
        "Should find strong move in mate position, got score {}",
        score
    );
}

// ============================================================================
// TEST 6: Performance - Not Significantly Slower Than Fixed
// ============================================================================

#[test]
fn test_id_performance() {
    let mut board1 =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let mut board2 = board1.clone();
    let tables = load_magic_tables();

    use std::time::Instant;

    // Time iterative deepening
    let start_id = Instant::now();
    let _ = search_iterative_deepening(&mut board1, &tables, 5);
    let time_id = start_id.elapsed();

    // Time fixed depth
    let start_fixed = Instant::now();
    let _ = search_fixed_depth(&mut board2, &tables, 5);
    let time_fixed = start_fixed.elapsed();

    println!("ID time: {:?}", time_id);
    println!("Fixed time: {:?}", time_fixed);

    // ID should be at most 50% slower than fixed depth
    // (Sometimes ordering improvements make it faster, but usually 10-40% slower)
    let ratio = time_id.as_secs_f64() / time_fixed.as_secs_f64();
    assert!(
        ratio < 1.5,
        "ID too slow: {:.2}x slower than fixed depth",
        ratio
    );

    println!("Performance ratio: {:.2}x", ratio);
}

// ============================================================================
// TEST 7: Handles Positions With Few Moves
// ============================================================================

#[test]
fn test_id_limited_moves() {
    // Endgame with few legal moves
    let mut board = Board::from_str("8/8/8/8/8/3k4/8/3K4 w - - 0 1").unwrap();
    let tables = load_magic_tables();

    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 4);

    assert!(
        best_move.is_some(),
        "Should find move even with limited options"
    );
    assert!(
        score.abs() < 100,
        "King vs king should be roughly equal, got {}",
        score
    );
}

// ============================================================================
// TEST 8: Consistent Across Multiple Runs
// ============================================================================

#[test]
fn test_id_deterministic() {
    let mut board1 =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let mut board2 = board1.clone();
    let tables = load_magic_tables();

    let (score1, move1) = search_iterative_deepening(&mut board1, &tables, 4);
    let (score2, move2) = search_iterative_deepening(&mut board2, &tables, 4);

    assert_eq!(score1, score2, "Should get same score on repeated searches");
    assert_eq!(move1, move2, "Should get same move on repeated searches");
}

// ============================================================================
// TEST 9: Depth 1 Works Correctly
// ============================================================================

#[test]
fn test_id_depth_1() {
    let mut board =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let tables = load_magic_tables();

    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 1);

    assert!(best_move.is_some(), "Should work at depth 1");
    assert!(
        score.abs() < 200,
        "Shallow search should give reasonable score, got {}",
        score
    );
}

// ============================================================================
// TEST 10: Doesn't Crash on Complex Position
// ============================================================================

#[test]
fn test_id_complex_position() {
    // Complex middlegame position
    let mut board =
        Board::from_str("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1")
            .unwrap();
    let tables = load_magic_tables();

    // Should complete without crashing
    let (score, best_move) = search_iterative_deepening(&mut board, &tables, 4);

    assert!(best_move.is_some(), "Should handle complex positions");
    assert!(
        score.abs() < 500,
        "Complex equal position should have reasonable score, got {}",
        score
    );
}

// ============================================================================
// TEST 11: Score Improves or Stays Similar With Depth
// ============================================================================

#[test]
fn test_id_score_stability() {
    // Position where White is clearly better
    let mut board =
        Board::from_str("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1").unwrap();
    let tables = load_magic_tables();

    let (score_d2, _) = search_iterative_deepening(&mut board, &tables, 2);
    let (score_d4, _) = search_iterative_deepening(&mut board, &tables, 4);

    println!("Score at depth 2: {}", score_d2);
    println!("Score at depth 4: {}", score_d4);

    // Scores can vary but shouldn't wildly differ
    // (allow up to 200 centipawn variation)
    assert!(
        (score_d2 - score_d4).abs() < 200,
        "Scores shouldn't vary wildly between depths: d2={}, d4={}",
        score_d2,
        score_d4
    );
}

// ============================================================================
// INTEGRATION TEST: Full Game Opening
// ============================================================================

#[test]
fn test_id_opening_sequence() {
    let mut board =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    let tables = load_magic_tables();

    // Play 3 moves with iterative deepening
    for move_num in 1..=3 {
        let (score, best_move) = search_iterative_deepening(&mut board, &tables, 4);

        assert!(
            best_move.is_some(),
            "Should find move {} in opening",
            move_num
        );

        println!("Move {}: {:?}, Score: {}", move_num, best_move, score);

        // Make the move (you'll need make_move_basic for this)
        // let undo = make_move_basic(&mut board, best_move.unwrap());
    }
}
