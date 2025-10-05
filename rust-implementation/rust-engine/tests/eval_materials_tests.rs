use rust_engine::board::Board;
use rust_engine::moves::magic::loader::load_magic_tables;
// We’re testing Step 1 only (material function), not static_eval yet:
use rust_engine::search::eval::{eval_material, static_eval};
use std::str::FromStr;

#[test]
fn startpos_material_is_zero() {
    // Ensure magics are initialized (common pattern in this repo)
    let _tables = load_magic_tables();
    let b = Board::new();
    assert_eq!(
        eval_material(&b),
        0,
        "Start position should have 0 material balance"
    );
}

#[test]
fn up_a_pawn_is_positive_and_mirroring_is_exact_negative() {
    let _tables = load_magic_tables();

    // White has an extra pawn (a3)
    let w_fen = "rnbqkbnr/1ppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    let bw = Board::from_str(w_fen).unwrap();
    let sw = eval_material(&bw);
    assert!(
        sw > 0,
        "White up a pawn should be positive for White, got {}",
        sw
    );

    // Mirror: Black has an extra pawn (a6)
    let b_fen = "rnbqkbnr/pppppppp/8/8/8/8/1PPPPPPP/RNBQKBNR b KQkq - 0 1";
    let bb = Board::from_str(b_fen).unwrap();
    let sb = eval_material(&bb);
    assert!(
        sb < 0,
        "Mirrored position should be negative for White, got {}",
        sb
    );

    assert_eq!(
        sw, -sb,
        "Material-only must mirror exactly: {} vs {}",
        sw, sb
    );
}

// Helpers: construct tiny positions via FEN so we don't depend on move plumbing.
// Assumes you have Board::from_fen(&str) -> Board (or similar).
fn fen(f: &str) -> Board {
    Board::from_str(f).expect("valid FEN")
}

#[test]
fn material_startpos_is_zero() {
    // Start position
    let b = fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    assert_eq!(eval_material(&b), 0);
    assert_eq!(static_eval(&b), 0); // should match material when psqt off or zero tables
}

#[test]
fn material_white_up_a_pawn_is_plus_100() {
    // Single white pawn vs empty
    let b = fen("8/8/8/8/8/8/P7/8 w - - 0 1");
    assert_eq!(eval_material(&b), 100);
    assert_eq!(static_eval(&b), 100);
}

#[test]
fn material_black_up_a_rook_is_minus_500() {
    // Single black rook vs empty
    let b = fen("8/8/8/8/8/8/8/7r w - - 0 1"); // h1 black rook (note: side to move doesn't matter for material)
    assert_eq!(eval_material(&b), -500);
    assert_eq!(static_eval(&b), -500);
}

#[test]
fn material_promotion_delta_is_plus_800_for_white() {
    // White pawn on a7 (about to promote) vs empty
    // let pawn_only = fen("P7/P7/P7/P7/P7/P7/P7/7K w - - 0 1"); // <- ignore; instead do minimal:
    // let pawn_pos = fen("P7/8/8/8/8/8/8/8 w - - 0 1"); // white pawn on a8 is illegal; use a7 then queen on a7

    // White pawn on a7
    let a7_pawn = fen("8/P7/8/8/8/8/8/8 w - - 0 1");
    // White queen on a7 (i.e., pawn promoted, pawn removed, queen added)
    let a7_queen = fen("8/Q7/8/8/8/8/8/8 w - - 0 1");

    let pawn_score = eval_material(&a7_pawn);
    let queen_score = eval_material(&a7_queen);
    assert_eq!(queen_score - pawn_score, 900 - 100); // +800
}

#[test]
fn material_en_passant_capture_reduces_white_pawns_by_one() {
    // Position with a legal EP against White: White pawn on e5, Black pawn on d5, EP square is d6 after e5xd6 ep by black
    // Easier: directly assert the count math with clear position after EP has been taken.
    // After EP capture (black captured a white pawn), we should be down 100 for White.
    let after_ep = fen("8/8/3p4/8/8/8/8/8 w - - 0 1"); // single black pawn on d6 (result square for black EP capture)
    // Compare to position where that white pawn still exists:
    let before_ep = fen("8/8/3p4/4P3/8/8/8/8 w - - 0 1");
    assert_eq!(eval_material(&before_ep) - eval_material(&after_ep), 100);
}

// -------------- PSQT plumbing (feature-gated) --------------

#[cfg(not(feature = "psqt"))]
#[test]
fn static_eval_equals_material_when_psqt_feature_is_off() {
    let b = fen("8/8/8/8/8/8/P7/8 w - - 0 1");
    assert_eq!(static_eval(&b), eval_material(&b));
}

#[cfg(feature = "psqt")]
#[test]
fn psqt_zero_tables_contribute_zero() {
    // Your PSQT arrays are [0;64], so PSQT must be 0 on arbitrary positions.
    let b1 = fen("8/8/8/8/8/8/P7/8 w - - 0 1");
    let b2 = fen("8/8/2n5/8/8/8/8/8 w - - 0 1");
    assert_eq!(static_eval(&b1), eval_material(&b1));
    assert_eq!(static_eval(&b2), eval_material(&b2));
}

// -------------- Mirror sanity (independent of PSQT tables) --------------

#[cfg(feature = "psqt")]
#[test]
fn mirror_vert_basic_checks() {
    use rust_engine::search::eval::mirror_vert; // make it pub(crate) or expose for tests
    // a2 <-> a7, c3 <-> c6, h1 <-> h8
    // Assuming a1=0..h8=63 (file + 8*rank)
    let a2 = rust_engine::square::Square::from_str("a2").unwrap().index();
    let a7 = rust_engine::square::Square::from_str("a7").unwrap().index();
    let c3 = rust_engine::square::Square::from_str("c3").unwrap().index();
    let c6 = rust_engine::square::Square::from_str("c6").unwrap().index();
    let h1 = rust_engine::square::Square::from_str("h1").unwrap().index();
    let h8 = rust_engine::square::Square::from_str("h8").unwrap().index();
    assert_eq!(mirror_vert(a2), a7);
    assert_eq!(mirror_vert(a7), a2);
    assert_eq!(mirror_vert(c3), c6);
    assert_eq!(mirror_vert(c6), c3);
    assert_eq!(mirror_vert(h1), h8);
    assert_eq!(mirror_vert(h8), h1);
}
