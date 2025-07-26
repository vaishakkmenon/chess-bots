use rust_engine::board::{Board, Color};
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::moves::movegen::generate_bishop_moves;
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

#[test]
fn bishop_moves_from_d4_empty_board() {
    let mut board = Board::new_empty();
    let d4 = 27;
    board.white_bishops = 1 << d4;
    board.side_to_move = Color::White;

    let magic_tables = load_magic_tables();
    let mut moves = Vec::new();
    generate_bishop_moves(&board, &magic_tables.bishop, &mut moves);

    let expected_dests = [18, 20, 9, 0, 36, 45, 54, 63, 34, 41, 48, 6, 13];
    assert_eq!(moves.len(), expected_dests.len());

    for &to in &expected_dests {
        assert!(
            moves.iter().any(|m| m.to.index() == to),
            "Missing move to square {}",
            to
        );
    }
}

#[test]
fn bishop_moves_from_corner_a1() {
    let mut board = Board::new_empty();
    let a1 = 0;
    board.white_bishops = 1 << a1;
    board.side_to_move = Color::White;

    let magic_tables = load_magic_tables();
    let mut moves = Vec::new();
    generate_bishop_moves(&board, &magic_tables.bishop, &mut moves);

    let expected_dests = [9, 18, 27, 36, 45, 54, 63];
    assert_eq!(moves.len(), expected_dests.len());

    for &to in &expected_dests {
        assert!(moves.iter().any(|m| m.to.index() == to));
    }
}

#[test]
fn bishop_blocked_by_friendly_piece() {
    let mut board = Board::new_empty();
    let d4 = 27;
    board.white_bishops = 1 << d4;
    board.white_pawns = 1 << 36; //  piece blocks one path
    board.side_to_move = Color::White;

    let magic_tables = load_magic_tables();
    let mut moves = Vec::new();
    generate_bishop_moves(&board, &magic_tables.bishop, &mut moves);

    // d4 has 12 moves on empty board, blocked at 36 removes one (plus all behind it)
    let expected_removed = 36;
    assert!(!moves.iter().any(|m| m.to.index() == expected_removed));
    assert!(moves.len() < 12);
}

#[test]
fn bishop_captures_enemy_piece() {
    let mut board = Board::new_empty();
    let d4 = 27;
    board.white_bishops = 1 << d4;
    board.black_rooks = 1 << 36;
    board.side_to_move = Color::White;

    let magic_tables = load_magic_tables();
    let mut moves = Vec::new();
    generate_bishop_moves(&board, &magic_tables.bishop, &mut moves);

    let mv = moves
        .iter()
        .find(|m| m.to.index() == 36)
        .expect("Expected capture move to 36");
    assert!(mv.is_capture);
}

#[test]
fn multiple_bishops_generate_moves() {
    let mut board = Board::new_empty();
    board.white_bishops = (1 << 2) | (1 << 20); // c1 and e3
    board.side_to_move = Color::White;

    let magic_tables = load_magic_tables();
    let mut moves = Vec::new();
    generate_bishop_moves(&board, &magic_tables.bishop, &mut moves);

    assert!(moves.iter().any(|m| m.from.index() == 2));
    assert!(moves.iter().any(|m| m.from.index() == 20));
    assert!(moves.len() > 0);
}

#[test]
fn no_bishops_yields_no_moves() {
    let mut board = Board::new_empty();
    board.side_to_move = Color::White;

    let magic_tables = load_magic_tables();
    let mut moves = Vec::new();
    generate_bishop_moves(&board, &magic_tables.bishop, &mut moves);

    assert!(moves.is_empty());
}
