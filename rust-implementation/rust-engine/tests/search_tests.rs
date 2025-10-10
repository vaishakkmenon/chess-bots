//! Minimal search wiring tests: depth-0 behavior, stalemate/checkmate behavior,
//! and a simple "free capture at depth=1" sanity check.
use rust_engine::board::Board;
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::search::eval::static_eval;
use rust_engine::search::search::search_fixed_depth;
use std::str::FromStr;

fn fen(f: &str) -> Board {
    Board::from_str(f).expect("valid FEN")
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

    // After capturing, white is up a pawn (material +100) plus PSQT bonuses
    assert!(
        score >= 100,
        "depth-1 should find exd5 gaining a pawn (+100 material minimum); got {}",
        score
    );
}

#[test]
fn test_quiescence_avoids_losing_queen() {
    // Position where Qxe5 looks good but loses the queen to Nxe5
    let mut board =
        Board::from_str("rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5Q2/PPPP1PPP/RNB1KBNR w KQkq - 0 1")
            .unwrap();

    let tables = load_magic_tables();
    let (score, _) = search_fixed_depth(&mut board, &tables, 3);

    // Should NOT think position is winning (Qxe5 loses queen)
    assert!(
        score < 500,
        "Should not think Qxe5 is winning, got {}",
        score
    );
}
