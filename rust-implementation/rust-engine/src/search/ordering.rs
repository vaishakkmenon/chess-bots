use crate::board::Board;
use crate::moves::types::Move;

pub fn mvv_lva_score(mv: Move, board: &Board) -> i32 {
    if let Some(captured) = board.piece_at(mv.to) {
        let captured_piece = captured.1;
        return captured_piece.value() * 10 - mv.piece.attacker_value();
    }
    0
}

pub fn order_moves(
    moves: &mut Vec<Move>,
    board: &Board,
    killer_moves: &[Option<Move>; 2],
    history: &[[i32; 64]; 64],
) {
    // stable sort so non-captures keep their generation order
    moves.sort_by_cached_key(|&mv| {
        // Priority 1: Captures (MVV-LVA)
        let capture_score = mvv_lva_score(mv, board);
        if capture_score > 0 {
            return -(10000 + capture_score);
        }

        // Priority 2: Killer moves
        if Some(mv) == killer_moves[0] {
            return -9000;
        }
        if Some(mv) == killer_moves[1] {
            return -8000;
        }

        // Priority 3: History heuristic
        -history[mv.from.index() as usize][mv.to.index() as usize]
    });
}
