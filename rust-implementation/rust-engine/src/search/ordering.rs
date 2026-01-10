use crate::board::Board;
use crate::moves::types::Move;

const CAPTURE_BASE: i32 = 10000;
const KILLER1_SCORE: i32 = 9000;
const KILLER2_SCORE: i32 = 8000;

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
    hash_move: Option<Move>,
) {
    // stable sort so non-captures keep their generation order
    moves.sort_by_cached_key(|&mv| {
        // Priority 0: Best move from previous iteration
        if Some(mv) == hash_move {
            return -100000; // Try this first!
        }

        // Priority 1: Captures (MVV-LVA)
        let capture_score = mvv_lva_score(mv, board);
        if capture_score > 0 {
            return -(CAPTURE_BASE + capture_score);
        }

        // Priority 2: Killer moves
        if Some(mv) == killer_moves[0] {
            return -KILLER1_SCORE;
        }
        if Some(mv) == killer_moves[1] {
            return -KILLER2_SCORE;
        }

        // Priority 3: History heuristic
        -history[mv.from.index() as usize][mv.to.index() as usize]
    });
}
