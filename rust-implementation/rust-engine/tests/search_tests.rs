//! Minimal search wiring tests: depth-0 behavior, stalemate/checkmate behavior,
//! and a simple "free capture at depth=1" sanity check.
use rust_engine::board::Board;
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::moves::types::Move;
use rust_engine::search::eval::static_eval;
use rust_engine::search::search::search_fixed_depth;
use std::str::FromStr;

fn fen(f: &str) -> Board {
    Board::from_str(f).expect("valid FEN")
}

/// Helper function to search and return score
fn search_position(f: &str, depth: i32) -> (i32, Option<Move>) {
    let mut board = fen(f);
    let tables = load_magic_tables();
    search_fixed_depth(&mut board, &tables, depth)
}

#[test]
fn depth0_equals_static_eval_white_up_pawn() {
    // White has a lone pawn; only kings otherwise
    // FEN: black king a8, white king g1, white pawn e4
    let mut b = fen("k7/8/8/8/4P3/8/8/6K1 w - - 0 1");
    let tables = load_magic_tables();
    let (score, _) = search_fixed_depth(&mut b, &tables, 0);

    // At depth 0, search should return static eval
    assert_eq!(score, static_eval(&b));

    // Material is 100, PSQT may add bonuses
    assert!(
        score >= 100,
        "White pawn (material=100) + PSQT bonuses should be >= 100, got {}",
        score
    );
}

#[test]
fn stalemate_returns_zero_any_depth() {
    // Classic stalemate: Black to move, not in check, no legal moves.
    // Position: Kh8, Qf7, Kg6. This is a well-known stalemate.
    let mut b = fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");
    let tables = load_magic_tables();
    for d in 0..=3 {
        let (score, _) = search_fixed_depth(&mut b, &tables, d);
        assert_eq!(score, 0, "stalemate should return 0 at depth {d}");
    }
}

#[test]
fn depth1_prefers_free_capture_white() {
    // White can capture a hanging pawn in one move (e4xd5) with no recapture.
    // Pieces: black king a8, white king g1, white pawn e4, black pawn d5.
    // Before: material = 0; After exd5: +100 (white up a pawn).
    let mut b = fen("k7/8/8/3p4/4P3/8/8/6K1 w - - 0 1");
    let tables = load_magic_tables();

    let (score, best_move) = search_fixed_depth(&mut b, &tables, 1);

    // Should find a move
    assert!(best_move.is_some(), "Should find a move at depth 1");

    // After capturing, white is up a pawn
    // Material: +100, PSQT: +5 (pawn on d5), Tempo: -10 (Black to move)
    // Expected score: 100 + 5 - 10 = 95
    assert!(
        score >= 90,
        "depth-1 should find exd5 gaining net ~95 (material +100, PSQT +5, tempo -10); got {}",
        score
    );
}
// ============================================================================
// CORE QUIESCENCE TESTS
// ============================================================================

#[test]
fn test_avoids_losing_queen_to_knight() {
    // White to move: Qxe5 looks like winning a pawn
    // But Black responds Nxe5, winning the queen
    let fen = "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5Q2/PPPP1PPP/RNB1KBNR w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score < 500,
        "Engine should not think Qxe5 is winning. Score: {} (expected < 500)",
        score
    );
}

#[test]
fn test_finds_winning_capture_sequence() {
    // White can win exchange: Bxf6 gxf6, winning bishop for knight
    let fen = "rnbqkb1r/pppp1ppp/5n2/4p1B1/4P3/8/PPPP1PPP/RN1QKBNR w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score > -100,
        "Should see Bxf6 sequence as at least equal. Score: {}",
        score
    );
}

#[test]
fn test_equal_trade_evaluation() {
    // Position where Nxe5 Nxe5 is an equal knight trade
    let fen = "rnbqkb1r/pppp1ppp/8/4p3/4n3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score.abs() < 150,
        "Equal trade should result in near-zero score. Score: {}",
        score
    );
}

#[test]
fn test_refuses_bad_queen_sacrifice() {
    // White queen can capture pawns but will be trapped
    let fen = "r1bqkbnr/ppp2ppp/2n5/3pp3/3PP3/2N2Q2/PPP2PPP/R1B1KBNR w KQkq - 0 1";

    let (score, _) = search_position(fen, 5);

    assert!(
        score < 400,
        "Should recognize queen sacrifice is bad. Score: {}",
        score
    );
}

#[test]
fn test_forced_capture_sequence() {
    // Position with forced captures
    let fen = "r2qr1k1/ppp2ppp/2n2n2/2bpp1B1/2P5/2N1PN2/PP2QPPP/2RR2K1 w - - 0 1";

    let (score_shallow, _) = search_position(fen, 3);
    let (score_deep, _) = search_position(fen, 5);

    let score_diff = (score_shallow - score_deep).abs();
    assert!(
        score_diff < 200,
        "Scores should be stable with quiescence. Depth 3: {}, Depth 5: {}",
        score_shallow,
        score_deep
    );
}

#[test]
fn test_queen_trade_evaluation() {
    // Position with equal material where queens can be traded
    let fen = "r1bqkb1r/ppppnppp/2n5/4p3/4P3/2N2N2/PPPPQPPP/R1B1KB1R w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score.abs() < 250,
        "Equal material position should be near-equal. Score: {}",
        score
    );
}

#[test]
fn test_hanging_piece_after_capture() {
    // Black knight on e4 is hanging, White can capture it
    let fen = "rnbqkb1r/pppp1ppp/8/8/4n3/2N5/PPPPPPPP/R1BQKBNR w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score > 250,
        "Should see hanging knight can be captured. Score: {}",
        score
    );
}

#[test]
fn test_desperado_captures() {
    // Knight on e5 is attacked and must move or trade
    let fen = "rnbqkb1r/pppp1ppp/5n2/4N3/8/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score.abs() < 1000,
        "Desperado tactics should be evaluated correctly. Score: {}",
        score
    );
}

#[test]
fn test_quiet_position_no_captures() {
    // Starting position - completely quiet
    let fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score.abs() < 100,
        "Starting position should be near equal. Score: {}",
        score
    );
}

#[test]
fn test_multiple_recaptures() {
    // Multiple pieces can recapture on same square
    let fen = "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score.abs() < 150,
        "Multiple recaptures should be evaluated correctly. Score: {}",
        score
    );
}

#[test]
fn test_quiescence_depth_limit() {
    // Position with many possible captures - should not hang
    let fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/3P1N2/PPP2PPP/RNBQKB1R w KQkq - 0 1";

    use std::time::Instant;
    let start = Instant::now();

    let (_score, _) = search_position(fen, 6);

    let elapsed = start.elapsed();
    assert!(
        elapsed.as_secs() < 10,
        "Quiescence should not cause excessive slowdown. Took: {:?}",
        elapsed
    );
}

#[test]
fn test_quiescence_with_checks() {
    // Black queen threatens checkmate, position is dangerous
    let fen = "rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    // Should handle checking positions without crashing
    assert!(
        score < 500,
        "Should handle checking positions. Score: {}",
        score
    );
}

#[test]
fn test_stand_pat_beta_cutoff() {
    // Position where standing pat is reasonable
    let fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score.abs() < 200,
        "Stand pat should work correctly. Score: {}",
        score
    );
}

#[test]
fn test_delta_pruning_correctness() {
    // Position where delta pruning is applied
    let fen = "rnbqkb1r/ppp2ppp/3p1n2/4p3/3PP3/2N5/PPP2PPP/R1BQKBNR w KQkq - 0 1";

    let (score, _) = search_position(fen, 4);

    assert!(
        score.abs() < 500,
        "Delta pruning should not break evaluation. Score: {}",
        score
    );
}

#[test]
fn test_tactical_win_material() {
    // White can play Nxe5 winning a pawn cleanly
    let fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 1";

    let (score, _) = search_position(fen, 5);

    assert!(
        score > -50,
        "Should find tactical advantage for White. Score: {}",
        score
    );
}
