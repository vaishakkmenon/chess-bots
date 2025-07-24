use rust_engine::board::{Board, Color};
use rust_engine::moves::movegen::generate_knight_moves;

#[test]
fn knight_moves_from_d4() {
    let mut board = Board::new_empty();
    let d4 = 27; // square index 27

    // Place a knight at d4 for White
    board.white_knights = 1u64 << d4;
    board.side_to_move = Color::White;

    let mut moves = Vec::new();
    generate_knight_moves(&board, &mut moves);

    let expected_dests = [
        10, 12, 17, 21, 33, 37, 42, 44, // valid knight jumps from d4
    ];

    assert_eq!(moves.len(), expected_dests.len());

    for dest in expected_dests {
        let found = moves.iter().any(|m| m.to.index() == dest);
        assert!(found, "Expected move to square {} not found", dest);
    }
}

#[test]
fn knight_moves_from_corner_a1() {
    let mut board = Board::new_empty();
    let a1 = 0;
    board.white_knights = 1 << a1;
    board.side_to_move = Color::White;

    let mut moves = Vec::new();
    generate_knight_moves(&board, &mut moves);

    let expected_dests = [10, 17];
    assert_eq!(moves.len(), expected_dests.len());

    for &to in &expected_dests {
        assert!(moves.iter().any(|m| m.to.index() == to));
    }
}

#[test]
fn knight_blocked_by_friendly_piece() {
    let mut board = Board::new_empty();
    let d4 = 27;
    board.white_knights = 1 << d4;
    board.white_pawns = 1 << 44; // Put pawn at one destination square
    board.side_to_move = Color::White;

    let mut moves = Vec::new();
    generate_knight_moves(&board, &mut moves);

    // Knight has 8 targets, 1 is blocked → expect 7 moves
    assert_eq!(moves.len(), 7);
    assert!(!moves.iter().any(|m| m.to.index() == 44));
}

#[test]
fn knight_captures_enemy_piece() {
    let mut board = Board::new_empty();
    let d4 = 27;
    board.white_knights = 1 << d4;
    board.black_rooks = 1 << 33; // valid knight destination
    board.side_to_move = Color::White;

    let mut moves = Vec::new();
    generate_knight_moves(&board, &mut moves);

    let mv = moves
        .iter()
        .find(|m| m.to.index() == 33)
        .expect("Missing capture");
    assert!(mv.is_capture);
}

#[test]
fn multiple_knights_generate_moves() {
    let mut board = Board::new_empty();
    board.white_knights = (1 << 1) | (1 << 18); // b1 and c3
    board.side_to_move = Color::White;

    let mut moves = Vec::new();
    generate_knight_moves(&board, &mut moves);
    println!("{:#?}", moves);
    // b1 has 2 moves, c3 has 8 → total 10
    assert_eq!(moves.len(), 9);
    assert!(moves.iter().any(|m| m.from.index() == 1));
    assert!(moves.iter().any(|m| m.from.index() == 18));
}

#[test]
fn no_knights_yields_no_moves() {
    let mut board = Board::new_empty();
    board.side_to_move = Color::White;

    let mut moves = Vec::new();
    generate_knight_moves(&board, &mut moves);

    assert!(moves.is_empty());
}
