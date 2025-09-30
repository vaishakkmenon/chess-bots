// tests/zobrist_tests.rs
use rust_engine::board::{Board, Color, Piece};
use rust_engine::hash::zobrist::zobrist_keys;
use rust_engine::{
    // move executor
    moves::execute::{make_move_basic, undo_move_basic},
    // if you keep the helper public, otherwise copy the check inline
    // hash::zobrist::zobrist_keys,
    square::Square,
};
use std::str::FromStr;

// Castling White Kingside
const CASTLE_WK: u8 = 0b0001;
// Castling White Queenside
const CASTLE_WQ: u8 = 0b0010;
// Castling Black Kingside
const CASTLE_BK: u8 = 0b0100;
// Castling Black Queenside
const CASTLE_BQ: u8 = 0b1000;

#[test]
fn zobrist_start_hash_stable() {
    let b = Board::new();
    assert_eq!(b.zobrist, b.compute_zobrist_full());
}

#[test]
fn zobrist_fen_recompute_stable() {
    let fens = &[
        // Start position
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        // After 1.e4: Black to move, EP square e3
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        // Kings + rooks only with all rights
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    ];

    for fen in fens {
        let mut b = Board::new_empty();
        b.set_fen(fen).expect("valid FEN");
        assert_eq!(b.zobrist, b.compute_zobrist_full(), "FEN: {fen}");
    }
}

#[test]
fn zobrist_castling_rights_toggle_changes_hash() {
    let mut b = Board::new();
    b.castling_rights = 0;
    b.refresh_zobrist();
    let h_none = b.zobrist;

    for (bit, name) in &[(0b0001u8, "K"), (0b0010, "Q"), (0b0100, "k"), (0b1000, "q")] {
        b.castling_rights = *bit;
        b.refresh_zobrist();
        assert_ne!(
            b.zobrist, h_none,
            "Enabling right {name} should change hash"
        );

        b.castling_rights = 0;
        b.refresh_zobrist();
        assert_eq!(
            b.zobrist, h_none,
            "Clearing right {name} should restore hash"
        );
    }
}

#[test]
fn zobrist_ep_capturable_differs_fen() {
    // Kings e1/e8, white pawn e4, black pawn d4. Black to move.
    // EP square e3 is capturable by the pawn on d4.
    let fen_with_ep = "4k3/8/8/8/3pP3/8/8/4K3 b KQkq e3 0 1";
    let fen_no_ep = "4k3/8/8/8/3pP3/8/8/4K3 b KQkq - 0 1";

    let mut b_ep = Board::new_empty();
    b_ep.set_fen(fen_with_ep).expect("FEN with EP");
    let h_ep = b_ep.zobrist;

    let mut b_no = Board::new_empty();
    b_no.set_fen(fen_no_ep).expect("FEN without EP");
    let h_no = b_no.zobrist;

    assert_ne!(h_ep, h_no, "Capturable EP should change the Zobrist hash");
}

#[test]
fn zobrist_side_to_move_xor_matches_recompute() {
    // 1) Start from any legal board (startpos here)
    let mut b = Board::new();
    let h0 = b.zobrist;

    // 2) Flip the side-to-move *without* touching anything else
    b.side_to_move = match b.side_to_move {
        Color::White => Color::Black,
        Color::Black => Color::White,
    };

    // 3) Full recompute is our ground truth
    let expected = b.compute_zobrist_full();

    // 4) Incremental rule: toggle exactly once with the side key
    let got = h0 ^ zobrist_keys().side_to_move;

    // 5) They must match
    assert_eq!(
        got, expected,
        "Side-to-move XOR must equal a full recompute after flipping the mover"
    );
}

#[allow(dead_code)]
fn mv(from: u8, to: u8, piece: Piece) -> rust_engine::moves::types::Move {
    rust_engine::moves::types::Move {
        from: Square::from_index(from),
        to: Square::from_index(to),
        piece,
        promotion: None,
        is_capture: false,
        is_castling: false,
        is_en_passant: false,
    }
}

#[test]
fn fen_parity_castling_variants() {
    let fens = [
        // pieces-only startpos with different castling rights
        "rn1qkbnr/pppbpppp/8/3p4/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 2 3",
        "rn1qkbnr/pppbpppp/8/3p4/3P4/5N2/PPP1PPPP/RNBQKB1R w K - 2 3",
        "rn1qkbnr/pppbpppp/8/3p4/3P4/5N2/PPP1PPPP/RNBQKB1R w Q - 2 3",
        "rn1qkbnr/pppbpppp/8/3p4/3P4/5N2/PPP1PPPP/RNBQKB1R w k - 2 3",
        "rn1qkbnr/pppbpppp/8/3p4/3P4/5N2/PPP1PPPP/RNBQKB1R w q - 2 3",
        "rn1qkbnr/pppbpppp/8/3p4/3P4/5N2/PPP1PPPP/RNBQKB1R w - - 2 3",
    ];
    for fen in fens {
        let b = Board::from_str(fen).expect("FEN parse");
        assert_eq!(
            b.zobrist,
            b.compute_zobrist_full(),
            "FEN parity failed: {fen}"
        );
    }
}

#[test]
fn castling_rights_clear_on_white_rook_moves() {
    // Startpos with full rights
    let mut b = Board::new();
    assert_eq!(
        b.castling_rights & (CASTLE_WK | CASTLE_WQ),
        CASTLE_WK | CASTLE_WQ
    );

    // a1 -> a2 clears WQ
    let u1 = make_move_basic(&mut b, mv(0, 8, Piece::Rook));
    assert_eq!(
        b.castling_rights & CASTLE_WQ,
        0,
        "WQ should be cleared after a1 rook moves"
    );
    assert_eq!(b.zobrist, b.compute_zobrist_full(), "parity after a1->a2");
    undo_move_basic(&mut b, u1);
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after undo a1->a2"
    );

    // h1 -> h2 clears WK
    let u2 = make_move_basic(&mut b, mv(7, 15, Piece::Rook));
    assert_eq!(
        b.castling_rights & CASTLE_WK,
        0,
        "WK should be cleared after h1 rook moves"
    );
    assert_eq!(b.zobrist, b.compute_zobrist_full(), "parity after h1->h2");
    undo_move_basic(&mut b, u2);
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after undo h1->h2"
    );
}

#[test]
fn castling_rights_clear_on_black_rook_moves() {
    let mut b = Board::new();
    // play a dummy full move so it's Black to move and we can move a8/h8 directly
    let u = make_move_basic(&mut b, mv(12, 20, Piece::Pawn)); // white: a2->a3
    undo_move_basic(&mut b, u); // optional; alternatively, push a white move then a black move properly

    // Move a8->a7 clears BQ
    // To get black move legally, do a minimal sequence:
    let _u_w = make_move_basic(&mut b, mv(12, 20, Piece::Pawn)); // a2->a3 (white)
    let u_b1 = make_move_basic(&mut b, mv(56, 48, Piece::Rook)); // a8->a7 (black)
    assert_eq!(
        b.castling_rights & CASTLE_BQ,
        0,
        "BQ should be cleared after a8 rook moves"
    );
    assert_eq!(b.zobrist, b.compute_zobrist_full(), "parity after a8->a7");
    undo_move_basic(&mut b, u_b1);
    undo_move_basic(&mut b, _u_w);
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after undo a8->a7"
    );

    // h8->h7 clears BK
    let _u_w2 = make_move_basic(&mut b, mv(13, 21, Piece::Pawn)); // b2->b3
    let u_b2 = make_move_basic(&mut b, mv(63, 55, Piece::Rook)); // h8->h7
    assert_eq!(
        b.castling_rights & CASTLE_BK,
        0,
        "BK should be cleared after h8 rook moves"
    );
    assert_eq!(b.zobrist, b.compute_zobrist_full(), "parity after h8->h7");
    undo_move_basic(&mut b, u_b2);
    undo_move_basic(&mut b, _u_w2);
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after undo h8->h7"
    );
}

#[test]
fn castling_rights_clear_on_king_move() {
    let mut b = Board::new();
    // e1 -> e2 clears both WK|WQ
    let u = make_move_basic(&mut b, mv(4, 12, Piece::King));
    assert_eq!(
        b.castling_rights & (CASTLE_WK | CASTLE_WQ),
        0,
        "white king moved → clear WK|WQ"
    );
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after king move"
    );
    undo_move_basic(&mut b, u);
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after undo king move"
    );
}

#[test]
fn castling_rights_clear_on_corner_rook_capture() {
    // Place a black piece that can capture the white rook on a1
    // let b = Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/1PPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    // Black bishop from c8 (58) to a6 (40) is not relevant; instead, we’ll just do a simple white move then black captures a1.
    // For simplicity: white plays a2->a3, black plays b4xa3? That's messy.
    // Easier: put a black rook on a2 in FEN and capture a1.
    let mut b =
        Board::from_str("rnbqkbnr/pppppppp/8/8/8/r7/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();
    // White passes with a light move
    let u_w = make_move_basic(&mut b, mv(12, 20, Piece::Pawn)); // a2->a3
    // Black: rook a3->a1 capturing rook on a1
    let u_b = make_move_basic(&mut b, mv(40, 0, Piece::Rook));
    assert_eq!(
        b.castling_rights & CASTLE_WQ,
        0,
        "captured rook on a1 → clear WQ"
    );
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after capture a1"
    );
    undo_move_basic(&mut b, u_b);
    undo_move_basic(&mut b, u_w);
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after undo capture a1"
    );
}

#[test]
fn castling_rights_do_not_return_when_rook_moves_back() {
    let mut b = Board::new();

    // a1->a2 clears WQ
    let u1 = make_move_basic(&mut b, mv(0, 8, Piece::Rook));
    assert_eq!(b.castling_rights & CASTLE_WQ, 0);
    assert_eq!(b.zobrist, b.compute_zobrist_full());

    // ... some moves to allow white to move again ...
    let u2 = make_move_basic(&mut b, mv(12, 20, Piece::Pawn)); // Black reply later, but keep parity checks simple:
    undo_move_basic(&mut b, u2); // just to balance if needed

    // a2->a1 (rights must stay cleared)
    let u3 = make_move_basic(&mut b, mv(8, 0, Piece::Rook));
    assert_eq!(b.castling_rights & CASTLE_WQ, 0, "rights must not return");
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after rook returns"
    );
    undo_move_basic(&mut b, u3);
    undo_move_basic(&mut b, u1);
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after full undo"
    );
}

#[test]
fn relaxed_ep_hashing_edges_white_double_push() {
    // White to move, black pawn on b4 -> after a2->a4, EP=a3 is capturable by Black
    let fen = "8/8/8/8/1p6/8/P6P/8 w - - 0 1"; // white pawns a2,h2; black pawn b4
    let mut b = Board::from_str(fen).unwrap();

    // a2->a4 (12->28)
    let u = make_move_basic(&mut b, mv(8, 24, Piece::Pawn));
    assert_eq!(b.en_passant.unwrap().index(), 16, "EP square should be a3");
    // EP should contribute to hash (b pawn on b4 can capture a3)
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after EP set (capturable)"
    );
    undo_move_basic(&mut b, u);
    assert_eq!(b.zobrist, b.compute_zobrist_full(), "parity after undo");
}

#[test]
fn relaxed_ep_hashing_edges_white_double_push_not_capturable() {
    // Same but without black pawn on b4 → EP should not contribute
    let fen = "8/8/8/8/8/8/P6P/8 w - - 0 1";
    let mut b = Board::from_str(fen).unwrap();

    let u = make_move_basic(&mut b, mv(8, 24, Piece::Pawn));
    assert_eq!(b.en_passant.unwrap().index(), 16, "EP square should be a3");
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity even when EP not capturable"
    );
    undo_move_basic(&mut b, u);
    assert_eq!(b.zobrist, b.compute_zobrist_full());
}

#[test]
fn relaxed_ep_hashing_edges_black_double_push() {
    // Black to move with white pawn on g4: after h7->h5, EP=h6 should be capturable by White
    let fen = "8/7p/8/6P1/8/8/8/8 b - - 0 1"; // black pawn h7, white pawn g5
    let mut b = Board::from_str(fen).unwrap();

    // h7->h5 (55->39) indices: h7=55, h5=39
    let u = make_move_basic(&mut b, mv(55, 39, Piece::Pawn));
    // EP should be h6 (index 47)
    assert_eq!(b.en_passant.unwrap().index(), 47, "EP square should be h6");
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity after EP set (capturable)"
    );
    undo_move_basic(&mut b, u);
    assert_eq!(b.zobrist, b.compute_zobrist_full());
}

#[test]
fn relaxed_ep_hashing_edges_black_double_push_not_capturable() {
    // Black double-push with no white pawn that can capture EP → EP not hashed
    let fen = "8/7p/8/8/8/8/8/8 b - - 0 1";
    let mut b = Board::from_str(fen).unwrap();

    let u = make_move_basic(&mut b, mv(55, 39, Piece::Pawn)); // h7->h5
    assert_eq!(b.en_passant.unwrap().index(), 47, "EP square should be h6");
    assert_eq!(
        b.zobrist,
        b.compute_zobrist_full(),
        "parity with non-capturable EP"
    );
    undo_move_basic(&mut b, u);
    assert_eq!(b.zobrist, b.compute_zobrist_full());
}
