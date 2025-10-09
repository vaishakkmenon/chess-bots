use crate::board::{Board, Color};
use crate::moves::execute::{generate_legal, make_move_basic, undo_move_basic};
use crate::moves::magic::MagicTables;
use crate::moves::square_control::in_check;
use crate::moves::types::Move;
use crate::search::eval::static_eval;
use crate::search::move_ordering::score_move;

pub const MATE: i32 = 30_000;
pub const INFTY: i32 = MATE + 2_000;

fn negamax(
    board: &mut Board,
    tables: &MagicTables,
    depth: i32,
    alpha: i32,
    beta: i32,
    ply: i32,
    scratch: &mut Vec<Move>,
) -> i32 {
    // Draw detection first
    if board.halfmove_clock >= 100 || board.repetition_count() >= 3 {
        return 0; // draw
    }

    // Generate legal moves ONCE
    let mut pseudo_scratch = Vec::with_capacity(256);
    scratch.clear();
    generate_legal(board, tables, scratch, &mut pseudo_scratch);

    // Terminal check
    if scratch.is_empty() {
        if in_check(board, board.side_to_move, tables) {
            return if board.side_to_move == Color::White {
                -(MATE - ply)
            } else {
                MATE - ply
            };
        }
        return 0; // stalemate
    }

    // Base case
    if depth == 0 {
        return static_eval(board);
    }

    // Sort moves by score (descending = best first)
    scratch.sort_unstable_by_key(|mv| {
        -score_move(mv, board) // Negative because we want descending order
    });

    // Copy moves locally since scratch will be reused in recursion
    let legal_moves: Vec<Move> = scratch.clone(); // ← Must clone before recursion

    let mut a = alpha;
    for &mv in legal_moves.iter() {
        let undo = make_move_basic(board, mv);
        let score = -negamax(board, tables, depth - 1, -beta, -a, ply + 1, scratch);
        undo_move_basic(board, undo);

        if score > a {
            a = score;
            if a >= beta {
                return a;
            }
        }
    }

    a
}

pub fn search_fixed_depth(board: &mut Board, tables: &MagicTables, depth: i32) -> i32 {
    debug_assert!(depth >= 0);
    let mut moves: Vec<Move> = Vec::with_capacity(64);
    negamax(board, tables, depth, -INFTY, INFTY, 0, &mut moves)
}
