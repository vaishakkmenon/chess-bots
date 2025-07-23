use rust_engine::board::{Board, Color};
use rust_engine::moves::movegen::generate_knight_moves;

#[test]
fn knight_moves_from_d4() {
    let mut board = Board::new_empty();
    let d4 = 3 + 8 * 3; // square index 27

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
