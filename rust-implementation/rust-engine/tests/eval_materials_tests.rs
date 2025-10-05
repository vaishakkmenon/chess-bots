use rust_engine::board::Board;
use rust_engine::moves::magic::loader::load_magic_tables;
// We’re testing Step 1 only (material function), not static_eval yet:
use rust_engine::search::eval::eval_material;
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
