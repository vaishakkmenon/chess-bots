use crate::board::Board;
use crate::moves::execute::{generate_legal, make_move_basic, undo_move_basic};
use crate::moves::magic::MagicTables;
use crate::moves::square_control::in_check;
use crate::moves::types::Move;
use crate::search::context::SearchContext;
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
    ply: usize,
    ctx: &mut SearchContext,
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
            return -(MATE - ply as i32); // Mated! Bad for current player
        }
        return 0; // stalemate
    }

    // Base case
    if depth == 0 {
        return static_eval(board);
    }

    // Sort moves by score (descending = best first)
    scratch.sort_unstable_by_key(|mv| {
        -score_move(mv, board, ctx, ply) // Negative because we want descending order
    });

    // Copy moves locally since scratch will be reused in recursion
    let legal_moves: Vec<Move> = scratch.clone(); // ← Must clone before recursion

    let mut a = alpha;
    for &mv in legal_moves.iter() {
        let undo = make_move_basic(board, mv);
        let score = -negamax(board, tables, depth - 1, -beta, -a, ply + 1, ctx, scratch);
        undo_move_basic(board, undo);

        if score > a {
            a = score;
            if a >= beta {
                // Beta cutoff!
                // Store killer if it's a quiet move
                if !mv.is_capture() {
                    ctx.update_killer(ply, mv); // ADD THIS LINE
                }
                return a;
            }
        }
    }

    a
}

pub fn search_fixed_depth(
    board: &mut Board,
    tables: &MagicTables,
    depth: i32,
) -> (i32, Option<Move>) {
    debug_assert!(depth >= 0);

    let mut ctx = SearchContext::new();
    let mut scratch = Vec::with_capacity(256);
    let mut pseudo_scratch = Vec::with_capacity(256);

    // Generate root moves
    scratch.clear();
    generate_legal(board, tables, &mut scratch, &mut pseudo_scratch);

    // No legal moves = checkmate or stalemate
    if scratch.is_empty() {
        return (0, None); // Return 0 score and no move
    }

    if depth == 0 {
        return (static_eval(board), None); // Immediate return, no search
    }
    // Sort root moves
    scratch.sort_unstable_by_key(|mv| -score_move(mv, board, &ctx, 0));

    let root_moves = scratch.clone();
    let mut best_score = -INFTY;
    let mut best_move = None;

    // Search each root move
    for &mv in root_moves.iter() {
        let undo = make_move_basic(board, mv);

        // Search with negated window (opponent's perspective)
        let score = -negamax(
            board,
            tables,
            depth - 1,
            -INFTY,
            INFTY,
            1,
            &mut ctx,
            &mut scratch,
        );

        undo_move_basic(board, undo);

        eprintln!("Move: {:?}, Score: {}", mv, score);

        // Track best move
        if score > best_score {
            best_score = score;
            best_move = Some(mv);
        }
    }

    (best_score, best_move)
}
