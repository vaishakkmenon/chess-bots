use crate::board::Board;
use crate::moves::types::Move;
use std::cmp::Reverse;

pub fn mvv_lva_score(mv: Move, board: &Board) -> i32 {
    if let Some(captured) = board.piece_at(mv.to) {
        let captured_piece = captured.1;
        return captured_piece.value() * 10 - mv.piece.attacker_value();
    }
    0
}

pub fn order_moves(moves: &mut Vec<Move>, board: &Board) {
    // stable sort so non-captures keep their generation order
    moves.sort_by_cached_key(|&mv| {
        // Give captures larger score; non-captures = 0
        // Sort descending (best captures first)
        Reverse(mvv_lva_score(mv, board))
    });
}
