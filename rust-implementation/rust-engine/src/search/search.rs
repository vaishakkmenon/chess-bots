use crate::board::Board;
use crate::moves::execute::{generate_legal, make_move_basic, undo_move_basic};
use crate::moves::magic::MagicTables;
use crate::moves::square_control::in_check;
use crate::moves::types::Move;
use crate::search::eval::static_eval;

pub fn minimax_basic(
    board: &mut Board,
    tables: &MagicTables,
    depth: i32,
    maximizing: bool,
) -> (i32, Option<Move>) {
    if depth == 0 {
        let score = static_eval(board);
        return (if maximizing { score } else { -score }, None);
    }

    let mut moves = Vec::with_capacity(128);
    let mut scratch = Vec::with_capacity(128);

    generate_legal(board, tables, &mut moves, &mut scratch);

    if moves.is_empty() {
        if in_check(board, board.side_to_move, tables) {
            // Checkmate
            return (if maximizing { -100000 } else { 100000 }, None);
        } else {
            // Stalemate
            return (0, None);
        }
    }

    let mut best_move = None;

    if maximizing {
        let mut max_eval = i32::MIN;
        for mv in moves {
            let undo = make_move_basic(board, mv);
            let (eval, _) = minimax_basic(board, tables, depth - 1, false);
            undo_move_basic(board, undo);

            if eval > max_eval {
                max_eval = eval;
                best_move = Some(mv);
            }
        }
        (max_eval, best_move)
    } else {
        let mut min_eval = i32::MAX;
        for mv in moves {
            let undo = make_move_basic(board, mv);
            let (eval, _) = minimax_basic(board, tables, depth - 1, true);
            undo_move_basic(board, undo);

            if eval < min_eval {
                min_eval = eval;
                best_move = Some(mv);
            }
        }
        (min_eval, best_move)
    }
}
