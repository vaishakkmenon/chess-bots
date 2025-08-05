use rust_engine::board::{Board, Color, Piece};
use rust_engine::moves::execute::{make_move_basic, undo_move_basic};
use rust_engine::moves::types::Move;
use rust_engine::square::Square;
use std::str::FromStr;

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

#[test]
fn roundtrip_pawn_capture() {
    let mut board = Board::new();
    let original = board.clone();

    // 1) White: e2 -> e4
    let mv1 = Move {
        from: Square::from_index(12), // e2
        to: Square::from_index(28),   // e4
        piece: Piece::Pawn,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    };
    let u1 = make_move_basic(&mut board, mv1);

    // 2) Black: d7 -> d5
    let mv2 = Move {
        from: Square::from_index(51), // d7
        to: Square::from_index(35),   // d5
        piece: Piece::Pawn,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    };
    let u2 = make_move_basic(&mut board, mv2);

    // 3) White captures: e4 -> d5
    let mv3 = Move {
        from: Square::from_index(28), // e4
        to: Square::from_index(35),   // d5
        piece: Piece::Pawn,
        promotion: None,
        is_capture: true,
        is_en_passant: false,
        is_castling: false,
    };
    let u3 = make_move_basic(&mut board, mv3);

    // Immediately after capture:
    // - The black pawn bitboard for d5 should no longer contain that square
    let mask_d5 = 1u64 << 35;
    assert_eq!(
        board.pieces(Piece::Pawn, Color::Black) & mask_d5,
        0,
        "Black pawn at d5 should have been cleared"
    );

    // - The white pawn bitboard for d5 should now contain that square
    assert_ne!(
        board.pieces(Piece::Pawn, Color::White) & mask_d5,
        0,
        "White pawn should now be on d5"
    );

    // - And piece_on_sq should reflect a white pawn at index 35
    let occ = board.piece_on_sq[35];
    let expected = ((Color::White as u8) << 3) | (Piece::Pawn as u8);
    assert_eq!(occ, expected, "piece_on_sq[35] should encode a White Pawn");

    // Now undo in reverse and verify full restoration
    undo_move_basic(&mut board, u3);
    undo_move_basic(&mut board, u2);
    undo_move_basic(&mut board, u1);
    assert_eq!(
        board, original,
        "Board should be back to the starting position"
    );
}

#[test]
fn roundtrip_white_kingside_castle() {
    let fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1";
    let mut b = Board::from_str(fen).unwrap();
    let original = b.clone();

    let mv = Move {
        from: Square::from_str("e1").unwrap(),
        to: Square::from_str("g1").unwrap(),
        piece: Piece::King,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: true,
    };
    let undo = make_move_basic(&mut b, mv);
    assert_ne!(b.pieces(Piece::King, Color::White) & (1 << 6), 0); // g1
    assert_ne!(b.pieces(Piece::Rook, Color::White) & (1 << 5), 0); // f1

    undo_move_basic(&mut b, undo);
    assert_eq!(b, original);
}
