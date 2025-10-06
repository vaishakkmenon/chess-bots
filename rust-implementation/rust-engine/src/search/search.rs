use crate::board::{Board, Color};
use crate::moves::execute::{generate_legal, make_move_basic, undo_move_basic};
use crate::moves::magic::MagicTables;
use crate::moves::square_control::in_check;
use crate::moves::types::Move;
use crate::search::eval::static_eval;

pub const MATE: i32 = 30_000;
pub const INFTY: i32 = MATE + 2_000;

fn is_terminal_fast(
    board: &mut Board,
    tables: &MagicTables,
    scratch: &mut Vec<Move>,
    ply: i32,
) -> Option<i32> {
    generate_legal(board, tables, scratch);
    if !scratch.is_empty() {
        return None;
    }

    let stm = board.side_to_move;
    if in_check(board, stm, tables) {
        return Some(if stm == Color::White {
            -(MATE - ply)
        } else {
            MATE - ply
        });
    }

    Some(0)
}

fn negamax(
    board: &mut Board,
    tables: &MagicTables,
    depth: i32,
    alpha: i32,
    beta: i32,
    ply: i32,
    scratch: &mut Vec<Move>,
) -> i32 {
    if let Some(tscore) = is_terminal_fast(board, tables, scratch, ply) {
        return tscore;
    }

    if depth == 0 {
        let score = static_eval(board);
        return if board.side_to_move == Color::White {
            score
        } else {
            -score
        };
    }
    let mut legal_moves: Vec<Move> = Vec::with_capacity(64);
    generate_legal(board, tables, &mut legal_moves);

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
