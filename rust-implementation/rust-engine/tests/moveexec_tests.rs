use rust_engine::board::{Board, Piece};
use rust_engine::moves::execute::{make_move_basic, undo_move_basic};
use rust_engine::moves::types::Move;
use rust_engine::square::Square;

#[test]
fn roundtrip_simple_move() {
    let mut b = Board::new();
    let before = b.clone();
    let mv = Move {
        from: Square::from_index(12),
        to: Square::from_index(20),
        piece: Piece::Pawn,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    };
    let undo = make_move_basic(&mut b, mv);
    undo_move_basic(&mut b, undo);
    assert_eq!(b, before);
}
