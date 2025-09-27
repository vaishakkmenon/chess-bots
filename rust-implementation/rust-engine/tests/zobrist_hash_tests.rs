// tests/zobrist_tests.rs
use rust_engine::board::{Board, Color};
use rust_engine::hash::zobrist::zobrist_keys; // adjust crate name if needed

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
