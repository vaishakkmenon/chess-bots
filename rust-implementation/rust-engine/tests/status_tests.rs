//! tests/status_tests.rs
//! Robust status tests using the status façade (no board->movegen imports)

use rust_engine::board::{Board, Piece};
use rust_engine::moves::execute::make_move_basic;
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::square::Square;
use rust_engine::status::{
    GameStatus, is_draw_by_fifty_move, is_draw_by_threefold, position_status,
};

// ---- Small helpers ----

#[inline]
fn sq(i: u8) -> Square {
    Square::from_index(i)
}

#[inline]
fn mv_king(from: u8, to: u8) -> rust_engine::moves::types::Move {
    rust_engine::moves::types::Move {
        from: sq(from),
        to: sq(to),
        piece: Piece::King,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    }
}

#[inline]
fn mv_pawn(from: u8, to: u8) -> rust_engine::moves::types::Move {
    rust_engine::moves::types::Move {
        from: sq(from),
        to: sq(to),
        piece: Piece::Pawn,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    }
}

// e1=4, d1=3; e2=12, f2=13 (a1=0 indexing)

#[test]
fn status_inplay_on_startpos() {
    let tables = load_magic_tables();
    let mut b = Board::new(); // start position
    // Start should not be an immediate draw or mate
    assert_eq!(position_status(&mut b, &tables), GameStatus::InPlay);
    assert!(!is_draw_by_threefold(&b));
    assert!(!is_draw_by_fifty_move(&b));
}

#[test]
fn status_draw_by_threefold() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    b.set_fen("8/8/8/8/8/8/4k3/R3K3 w - - 0 1").unwrap();

    // 1st cycle
    let _ = make_move_basic(&mut b, mv_king(4, 3)); // W: Ke1-d1
    let _ = make_move_basic(&mut b, mv_king(12, 11)); // B: Ke2-d2
    let _ = make_move_basic(&mut b, mv_king(3, 4)); // W: Kd1-e1
    let _ = make_move_basic(&mut b, mv_king(11, 12)); // B: Kd2-e2

    // 2nd cycle → third occurrence of start key
    let _ = make_move_basic(&mut b, mv_king(4, 3));
    let _ = make_move_basic(&mut b, mv_king(12, 11));
    let _ = make_move_basic(&mut b, mv_king(3, 4));
    let _ = make_move_basic(&mut b, mv_king(11, 12));

    assert_eq!(position_status(&mut b, &tables), GameStatus::DrawThreefold);
}

#[test]
fn status_draw_by_fifty_move_rule() {
    let tables = load_magic_tables();
    let mut b = Board::new();

    // Bare kings, White to move, halfmove clock already at 99
    // FEN fields: <pieces> <stm> <castling> <ep> <halfmove> <fullmove>
    b.set_fen("8/8/8/8/8/8/4k3/R3K3 w - - 99 50").unwrap();

    // Not a draw yet at 99 half-moves
    assert_eq!(position_status(&mut b, &tables), GameStatus::InPlay);

    // One reversible half-move → halfmove_clock becomes 100
    // e1 (4) -> d1 (3)
    let _ = make_move_basic(&mut b, mv_king(4, 3));

    // Now it *must* be a 50-move draw
    assert_eq!(position_status(&mut b, &tables), GameStatus::DrawFiftyMove);
}

#[test]
fn status_threefold_takes_priority_over_fifty_move() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // Add a rook to avoid dead position; set halfmove=92 so +8 plies => 100.
    b.set_fen("8/8/8/8/8/8/4k3/R3K3 w - - 92 50").unwrap();

    // 1st cycle → second occurrence of the start key
    let _ = make_move_basic(&mut b, mv_king(4, 3)); // W: Ke1-d1
    let _ = make_move_basic(&mut b, mv_king(12, 11)); // B: Ke2-d2
    let _ = make_move_basic(&mut b, mv_king(3, 4)); // W: Kd1-e1
    let _ = make_move_basic(&mut b, mv_king(11, 12)); // B: Kd2-e2

    // 2nd cycle → third occurrence (threefold) and halfmove_clock hits 100
    let _ = make_move_basic(&mut b, mv_king(4, 3));
    let _ = make_move_basic(&mut b, mv_king(12, 11));
    let _ = make_move_basic(&mut b, mv_king(3, 4));
    let _ = make_move_basic(&mut b, mv_king(11, 12));

    // Threefold should take precedence over the 50-move rule
    assert_eq!(position_status(&mut b, &tables), GameStatus::DrawThreefold);
}

#[test]
fn status_stalemate_detection() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // Stalemate: Black to move, not in check, no legal moves:
    // Black king h8 (63), White king g6 (46), White queen f7 (45).
    // FEN: 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1
    b.set_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1").unwrap();

    assert_eq!(position_status(&mut b, &tables), GameStatus::Stalemate);
}

#[test]
fn status_checkmate_detection() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // Checkmate: Black to move, in check, no legal moves:
    // Black king h8 (63), White king g6 (46), White queen g7 (54).
    // FEN: 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1
    b.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1").unwrap();

    assert_eq!(position_status(&mut b, &tables), GameStatus::Checkmate);
}

#[test]
fn status_no_false_draw_with_irreversible_reset() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // White pawn on d2, bare kings; after a reversible mini-cycle, push d2->d3 to reset
    b.set_fen("8/8/8/8/8/8/3Pk3/4K3 w - - 0 1").unwrap();

    // reversible mini-cycle (avoid capturing the pawn: Black uses e2<->f2)
    let _ = make_move_basic(&mut b, mv_king(4, 3)); // W: Ke1-d1
    let _ = make_move_basic(&mut b, mv_king(12, 13)); // B: Ke2-f2
    let _ = make_move_basic(&mut b, mv_king(3, 4)); // W: Kd1-e1
    let _ = make_move_basic(&mut b, mv_king(13, 12)); // B: Kf2-e2

    // irreversible pawn push d2 (11) -> d3 (19)
    let _ = make_move_basic(&mut b, mv_pawn(11, 19));
    // Immediately after, not a draw; window was truncated
    assert_eq!(position_status(&mut b, &tables), GameStatus::InPlay);
}

// ───────────────────────────────────────────────────────────────────────────
// Fivefold repetition (automatic)
// Start: bare kings; 4 full cycles = 5 occurrences of the start key (automatic draw)
// ───────────────────────────────────────────────────────────────────────────
#[test]
fn status_draw_by_fivefold_is_automatic() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    b.set_fen("8/8/8/8/8/8/4k3/R3K3 w - - 0 1").unwrap();

    for _ in 0..4 {
        let _ = make_move_basic(&mut b, mv_king(4, 3)); // W: Ke1-d1
        let _ = make_move_basic(&mut b, mv_king(12, 11)); // B: Ke2-d2
        let _ = make_move_basic(&mut b, mv_king(3, 4)); // W: Kd1-e1
        let _ = make_move_basic(&mut b, mv_king(11, 12)); // B: Kd2-e2
    }

    assert_eq!(position_status(&mut b, &tables), GameStatus::DrawFivefold);
}

// ───────────────────────────────────────────────────────────────────────────
// 75-move rule (automatic)
// Use FEN with halfmove clock at 149; one quiet move → 150 (automatic draw).
// ───────────────────────────────────────────────────────────────────────────
#[test]
fn status_draw_by_seventyfive_move_is_automatic() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    b.set_fen("8/8/8/8/8/8/4k3/4K3 w - - 149 50").unwrap();

    // One reversible half-move (e1→d1) -> halfmove_clock becomes 150
    let _ = make_move_basic(&mut b, mv_king(4, 3));

    assert_eq!(
        position_status(&mut b, &tables),
        GameStatus::DrawSeventyFiveMove
    );
}

// ───────────────────────────────────────────────────────────────────────────
// Priority: if both automatic thresholds are met, fivefold takes precedence.
// We get near 75, then perform cycles to reach fivefold too.
// ───────────────────────────────────────────────────────────────────────────
#[test]
fn status_priority_fivefold_over_seventyfive() {
    let tables = load_magic_tables();
    let mut b = Board::new();

    // Start close to 75-move threshold but not yet there.
    b.set_fen("8/8/8/8/8/8/4k3/R3K3 w - - 146 50").unwrap();
    // 1 ply -> 147
    let _ = make_move_basic(&mut b, mv_king(4, 3));
    // Now do cycles to push both repetition count high and halfmove over 150
    for _ in 0..4 {
        let _ = make_move_basic(&mut b, mv_king(12, 11));
        let _ = make_move_basic(&mut b, mv_king(3, 4));
        let _ = make_move_basic(&mut b, mv_king(11, 12));
        let _ = make_move_basic(&mut b, mv_king(4, 3));
    }

    // Fivefold should be chosen over 75-move
    assert_eq!(position_status(&mut b, &tables), GameStatus::DrawFivefold);
}

// ───────────────────────────────────────────────────────────────────────────
// Dead positions (insufficient material) → DrawDeadPosition
// ───────────────────────────────────────────────────────────────────────────

#[test]
fn dead_position_k_vs_k() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // Already bare kings
    b.set_fen("8/8/8/8/8/8/4k3/4K3 w - - 0 1").unwrap();
    assert_eq!(
        position_status(&mut b, &tables),
        GameStatus::DrawDeadPosition
    );
}

#[test]
fn dead_position_kn_vs_k() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // White N on d3 (19)
    b.set_fen("8/8/8/8/8/3N4/4k3/4K3 w - - 0 1").unwrap();
    assert_eq!(
        position_status(&mut b, &tables),
        GameStatus::DrawDeadPosition
    );
}

#[test]
fn dead_position_kb_vs_k() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // White B on d3 (19)
    b.set_fen("8/8/8/8/8/3B4/4k3/4K3 w - - 0 1").unwrap();
    assert_eq!(
        position_status(&mut b, &tables),
        GameStatus::DrawDeadPosition
    );
}

#[test]
fn dead_position_knn_vs_k() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // White knights on c3 (18) and d3 (19)
    b.set_fen("8/8/8/8/8/2N5/3N4/4k2K w - - 0 1").unwrap();
    assert_eq!(
        position_status(&mut b, &tables),
        GameStatus::DrawDeadPosition
    );
}

#[test]
fn dead_position_kn_vs_kn() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // White N on c3 (18), Black n on g1 (6) (any split-minor case is dead)
    b.set_fen("8/8/8/8/8/2N5/4k3/5n1K w - - 0 1").unwrap();
    assert_eq!(
        position_status(&mut b, &tables),
        GameStatus::DrawDeadPosition
    );
}

#[test]
fn dead_position_kb_vs_kb() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // White B on c3 (18), Black b on g1 (6)
    b.set_fen("8/8/8/8/8/2B5/4k3/5b1K w - - 0 1").unwrap();
    assert_eq!(
        position_status(&mut b, &tables),
        GameStatus::DrawDeadPosition
    );
}

// ───────────────────────────────────────────────────────────────────────────
// Not dead: still mating material (guards against false positives)
// ───────────────────────────────────────────────────────────────────────────

#[test]
fn not_dead_kbb_vs_k() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // Two bishops vs bare king: mating material exists
    b.set_fen("8/8/8/8/8/2B5/2B1k3/4K3 w - - 0 1").unwrap();
    assert_eq!(position_status(&mut b, &tables), GameStatus::InPlay);
}

#[test]
fn not_dead_kbn_vs_k() {
    let tables = load_magic_tables();
    let mut b = Board::new();
    // Bishop + Knight vs bare king: mating material exists
    b.set_fen("8/8/8/8/8/2B5/2N1k3/4K3 w - - 0 1").unwrap();
    assert_eq!(position_status(&mut b, &tables), GameStatus::InPlay);
}
