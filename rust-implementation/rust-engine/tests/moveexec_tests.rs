use rust_engine::board::{Board, Color, Piece};
use rust_engine::moves::execute::{make_move_basic, undo_move_basic};
use rust_engine::moves::types::Move;
use rust_engine::square::Square;
use std::str::FromStr;

pub(crate) const EMPTY_SQ: u8 = 0xFF;

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

#[test]
fn roundtrip_white_queenside_castle() {
    use std::str::FromStr;

    let fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1";
    let mut board = Board::from_str(fen).unwrap();
    let original = board.clone();

    let mv = Move {
        from: Square::from_str("e1").unwrap(),
        to: Square::from_str("c1").unwrap(),
        piece: Piece::King,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: true,
    };

    let undo = make_move_basic(&mut board, mv);

    assert_ne!(board.pieces(Piece::King, Color::White) & (1 << 2), 0); // c1
    assert_ne!(board.pieces(Piece::Rook, Color::White) & (1 << 3), 0); // d1

    undo_move_basic(&mut board, undo);
    assert_eq!(board, original);
}

#[test]
fn roundtrip_black_kingside_castle() {
    use std::str::FromStr;

    let fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1";
    let mut board = Board::from_str(fen).unwrap();
    board.side_to_move = Color::Black; // force black to move
    let original = board.clone();

    let mv = Move {
        from: Square::from_str("e8").unwrap(),
        to: Square::from_str("g8").unwrap(),
        piece: Piece::King,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: true,
    };

    let undo = make_move_basic(&mut board, mv);

    assert_ne!(board.pieces(Piece::King, Color::Black) & (1 << 62), 0); // g8
    assert_ne!(board.pieces(Piece::Rook, Color::Black) & (1 << 61), 0); // f8

    undo_move_basic(&mut board, undo);
    assert_eq!(board, original);
}

#[test]
fn roundtrip_black_queenside_castle() {
    use std::str::FromStr;

    let fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1";
    let mut board = Board::from_str(fen).unwrap();
    board.side_to_move = Color::Black; // force black to move
    let original = board.clone();

    let mv = Move {
        from: Square::from_str("e8").unwrap(),
        to: Square::from_str("c8").unwrap(),
        piece: Piece::King,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: true,
    };

    let undo = make_move_basic(&mut board, mv);

    assert_ne!(board.pieces(Piece::King, Color::Black) & (1 << 58), 0); // c8
    assert_ne!(board.pieces(Piece::Rook, Color::Black) & (1 << 59), 0); // d8

    undo_move_basic(&mut board, undo);
    assert_eq!(board, original);
}

#[test]
fn castling_rights_removed_on_king_move() {
    use rust_engine::board::{Board, Color};
    use std::str::FromStr;

    let fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1";
    let mut board = Board::from_str(fen).unwrap();

    assert!(board.has_kingside_castle(Color::White));
    assert!(board.has_queenside_castle(Color::White));

    let mv = Move {
        from: Square::from_str("e1").unwrap(),
        to: Square::from_str("f1").unwrap(),
        piece: Piece::King,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    };

    let undo = make_move_basic(&mut board, mv);

    assert!(!board.has_kingside_castle(Color::White));
    assert!(!board.has_queenside_castle(Color::White));

    undo_move_basic(&mut board, undo);

    assert!(board.has_kingside_castle(Color::White));
    assert!(board.has_queenside_castle(Color::White));
}

#[test]
fn castling_rights_removed_on_rook_move() {
    use rust_engine::board::{Board, Color};
    use std::str::FromStr;

    let fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1";
    let mut board = Board::from_str(fen).unwrap();

    assert!(board.has_kingside_castle(Color::White));
    assert!(board.has_queenside_castle(Color::White));

    let mv = Move {
        from: Square::from_str("h1").unwrap(),
        to: Square::from_str("h2").unwrap(),
        piece: Piece::Rook,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    };

    let undo = make_move_basic(&mut board, mv);

    assert!(!board.has_kingside_castle(Color::White));
    assert!(board.has_queenside_castle(Color::White));

    undo_move_basic(&mut board, undo);

    assert!(board.has_kingside_castle(Color::White));
    assert!(board.has_queenside_castle(Color::White));
}

#[test]
fn castling_rights_removed_on_rook_capture() {
    use rust_engine::board::{Board, Color};
    use std::str::FromStr;

    let fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1";
    let mut board = Board::from_str(fen).unwrap();

    // Move a black bishop to capture a white rook on a1
    board.side_to_move = Color::Black;

    let mv = Move {
        from: Square::from_str("e8").unwrap(), // Pretend this is a bishop
        to: Square::from_str("a1").unwrap(),
        piece: Piece::Bishop,
        promotion: None,
        is_capture: true,
        is_en_passant: false,
        is_castling: false,
    };

    assert!(board.has_queenside_castle(Color::White));

    let undo = make_move_basic(&mut board, mv);

    assert!(!board.has_queenside_castle(Color::White));

    undo_move_basic(&mut board, undo);

    assert!(board.has_queenside_castle(Color::White));
}

#[test]
fn roundtrip_en_passant_correct() {
    let mut board = Board::new();
    let original = board.clone();

    // 1) White: e2 -> e4
    let mv1 = Move {
        from: Square::from_str("e2").unwrap(),
        to: Square::from_str("e4").unwrap(),
        piece: Piece::Pawn,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    };
    let u1 = make_move_basic(&mut board, mv1);

    // 2) Black: a7 -> a6 (dummy move so White can play e4->e5)
    let mv2 = Move {
        from: Square::from_str("a7").unwrap(),
        to: Square::from_str("a6").unwrap(),
        piece: Piece::Pawn,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    };
    let u2 = make_move_basic(&mut board, mv2);

    // 3) White: e4 -> e5
    let mv3 = Move {
        from: Square::from_str("e4").unwrap(),
        to: Square::from_str("e5").unwrap(),
        piece: Piece::Pawn,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    };
    let u3 = make_move_basic(&mut board, mv3);

    // 4) Black: d7 -> d5 (double push; EP target = d6)
    let mv4 = Move {
        from: Square::from_str("d7").unwrap(),
        to: Square::from_str("d5").unwrap(),
        piece: Piece::Pawn,
        promotion: None,
        is_capture: false,
        is_en_passant: false,
        is_castling: false,
    };
    let u4 = make_move_basic(&mut board, mv4);

    // 5) White: e5xd6 en passant (captures the pawn that moved d7->d5)
    let mv5 = Move {
        from: Square::from_str("e5").unwrap(),
        to: Square::from_str("d6").unwrap(),
        piece: Piece::Pawn,
        promotion: None,
        is_capture: true,
        is_en_passant: true,
        is_castling: false,
    };
    let u5 = make_move_basic(&mut board, mv5);

    // After EP: white pawn on d6, black pawn removed from d5
    let d6 = Square::from_str("d6").unwrap().index();
    let d5 = Square::from_str("d5").unwrap().index();
    let mask_d6 = 1u64 << d6;
    let mask_d5 = 1u64 << d5;

    assert_ne!(
        board.pieces(Piece::Pawn, Color::White) & mask_d6,
        0,
        "white pawn should be on d6"
    );
    assert_eq!(
        board.pieces(Piece::Pawn, Color::Black) & mask_d5,
        0,
        "black pawn should be gone from d5"
    );

    // piece_on_sq: d6 has white pawn, d5 is empty
    let expected_white_pawn = ((Color::White as u8) << 3) | (Piece::Pawn as u8);
    assert_eq!(
        board.piece_on_sq[d6 as usize], expected_white_pawn,
        "d6 should encode a White Pawn"
    );
    assert_eq!(
        board.piece_on_sq[d5 as usize], EMPTY_SQ,
        "d5 should be empty after EP"
    );

    // Undo sequence
    undo_move_basic(&mut board, u5);
    undo_move_basic(&mut board, u4);
    undo_move_basic(&mut board, u3);
    undo_move_basic(&mut board, u2);
    undo_move_basic(&mut board, u1);

    assert_eq!(
        board, original,
        "Board should be back to start after EP roundtrip"
    );
}

#[test]
fn halfmove_and_fullmove_counters_with_ep() {
    let mut board = Board::new();
    let orig_half = board.halfmove_clock;
    let orig_full = board.fullmove_number;

    // White: e2->e4 (pawn move resets halfmove)
    let u1 = make_move_basic(
        &mut board,
        Move {
            from: Square::from_str("e2").unwrap(),
            to: Square::from_str("e4").unwrap(),
            piece: Piece::Pawn,
            promotion: None,
            is_capture: false,
            is_en_passant: false,
            is_castling: false,
        },
    );
    assert_eq!(board.halfmove_clock, 0);
    assert_eq!(board.fullmove_number, orig_full); // increments only after Black's move

    // Black: a7->a6 (pawn move resets halfmove, and increments fullmove)
    let u2 = make_move_basic(
        &mut board,
        Move {
            from: Square::from_str("a7").unwrap(),
            to: Square::from_str("a6").unwrap(),
            piece: Piece::Pawn,
            promotion: None,
            is_capture: false,
            is_en_passant: false,
            is_castling: false,
        },
    );
    assert_eq!(board.halfmove_clock, 0);
    assert_eq!(board.fullmove_number, orig_full + 1);

    // White: e4->e5 (pawn move resets halfmove)
    let u3 = make_move_basic(
        &mut board,
        Move {
            from: Square::from_str("e4").unwrap(),
            to: Square::from_str("e5").unwrap(),
            piece: Piece::Pawn,
            promotion: None,
            is_capture: false,
            is_en_passant: false,
            is_castling: false,
        },
    );
    assert_eq!(board.halfmove_clock, 0);
    assert_eq!(board.fullmove_number, orig_full + 1);

    // Black: d7->d5 (pawn move resets halfmove, increments fullmove)
    let u4 = make_move_basic(
        &mut board,
        Move {
            from: Square::from_str("d7").unwrap(),
            to: Square::from_str("d5").unwrap(),
            piece: Piece::Pawn,
            promotion: None,
            is_capture: false,
            is_en_passant: false,
            is_castling: false,
        },
    );
    assert_eq!(board.halfmove_clock, 0);
    assert_eq!(board.fullmove_number, orig_full + 2);

    // White: e5xd6 en passant (capture resets halfmove)
    let u5 = make_move_basic(
        &mut board,
        Move {
            from: Square::from_str("e5").unwrap(),
            to: Square::from_str("d6").unwrap(),
            piece: Piece::Pawn,
            promotion: None,
            is_capture: true,
            is_en_passant: true,
            is_castling: false,
        },
    );
    assert_eq!(board.halfmove_clock, 0);
    assert_eq!(board.fullmove_number, orig_full + 2); // still same; increments after Black moves

    // Undo all and verify counters restored
    undo_move_basic(&mut board, u5);
    undo_move_basic(&mut board, u4);
    undo_move_basic(&mut board, u3);
    undo_move_basic(&mut board, u2);
    undo_move_basic(&mut board, u1);

    assert_eq!(board.halfmove_clock, orig_half);
    assert_eq!(board.fullmove_number, orig_full);
}
