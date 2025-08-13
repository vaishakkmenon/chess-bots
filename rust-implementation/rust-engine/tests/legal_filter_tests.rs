use std::str::FromStr;

use rust_engine::board::Board;
use rust_engine::moves::execute::generate_legal;
use rust_engine::moves::magic::{MagicTableSeed, generate_magic_tables};
use rust_engine::moves::types::Move;
use rust_engine::square::Square;

fn tables() -> rust_engine::moves::magic::MagicTables {
    generate_magic_tables(MagicTableSeed::Fixed(42)).unwrap()
}

fn has_move(moves: &[Move], from: &str, to: &str) -> bool {
    let f = Square::from_str(from).unwrap();
    let t = Square::from_str(to).unwrap();
    moves.iter().any(|m| m.from == f && m.to == t)
}

#[test]
fn self_check_is_filtered_out() {
    // White: Ke1, Re2. Black: Re8. Moving Re2->f2 exposes e-file → illegal.
    let fen = "4r3/8/8/8/8/8/4R3/4K3 w - - 0 1";
    let mut b = Board::from_str(fen).unwrap();
    let t = tables();

    let mut legal = vec![];
    generate_legal(&mut b, &t, &mut legal);

    assert!(
        !has_move(&legal, "e2", "f2"),
        "Move e2f2 should be filtered (self-check)."
    );
    assert!(
        has_move(&legal, "e2", "e3"),
        "Blocking move e2e3 should remain legal."
    );
}

#[test]
fn checking_moves_are_kept() {
    // White: Re1, Kh1. Black: Ke8, Ne7. Re1xE7+ should be legal.
    let fen = "4k3/4n3/8/8/8/8/8/4R2K w - - 0 1";
    let mut b = Board::from_str(fen).unwrap();
    let t = tables();

    let mut legal = vec![];
    generate_legal(&mut b, &t, &mut legal);

    assert!(
        has_move(&legal, "e1", "e7"),
        "Checking capture e1e7 should not be filtered out."
    );
}
