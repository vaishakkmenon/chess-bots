use crate::board::Board;
use crate::moves::execute::{generate_legal, make_move_basic, undo_move_basic};
use crate::moves::magic::MagicTables;
use crate::moves::square_control::in_check;
use crate::moves::types::Move;
use crate::search::context::SearchContext;
use crate::search::eval::static_eval;
use crate::search::ordering::order_moves;
use crate::search::tt::{NodeType, TranspositionTable};
pub fn minimax(
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
        }

        // Stalemate
        return (0, None);
    }

    let mut best_move = None;

    if maximizing {
        let mut max_eval = i32::MIN;
        for mv in moves {
            let undo = make_move_basic(board, mv);
            let (eval, _) = minimax(board, tables, depth - 1, false);
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
            let (eval, _) = minimax(board, tables, depth - 1, true);
            undo_move_basic(board, undo);

            if eval < min_eval {
                min_eval = eval;
                best_move = Some(mv);
            }
        }
        (min_eval, best_move)
    }
}

pub fn alpha_beta(
    board: &mut Board,
    tables: &MagicTables,
    ctx: &mut SearchContext,
    tt: &mut TranspositionTable,
    depth: i32,
    ply: usize,
    mut alpha: i32,
    beta: i32,
) -> (i32, Option<Move>) {
    let hash = board.zobrist;

    // Probe TT
    if let Some(entry) = tt.probe(hash) {
        if entry.depth >= depth as i8 {
            match entry.node_type {
                NodeType::Exact => return (entry.score, entry.best_move),
                NodeType::LowerBound if entry.score >= beta => return (beta, entry.best_move),
                NodeType::UpperBound if entry.score <= alpha => return (alpha, entry.best_move),
                _ => {}
            }
        }
    }

    if depth == 0 {
        return (static_eval(board), None);
    }

    let mut moves = Vec::with_capacity(128);
    let mut scratch = Vec::with_capacity(128);

    generate_legal(board, tables, &mut moves, &mut scratch);
    order_moves(&mut moves, board, &ctx.killer_moves[ply], &ctx.history);

    if moves.is_empty() {
        if in_check(board, board.side_to_move, tables) {
            // Checkmate
            // Depth matters, closer to checkmate is preferred
            return (-100000 + depth, None);
        }

        //Stalemate
        return (0, None);
    }

    let mut best_move = None;
    let original_alpha = alpha;

    for mv in moves {
        let undo = make_move_basic(board, mv);
        let (score, _) = alpha_beta(board, tables, ctx, tt, depth - 1, ply + 1, -beta, -alpha);
        let score = -score;
        undo_move_basic(board, undo);

        if score >= beta {
            // Beta cutoff
            ctx.update_killer(ply, mv);
            ctx.update_history(mv, depth);
            return (beta, Some(mv));
        }

        if score > alpha {
            alpha = score;
            best_move = Some(mv);
            ctx.update_history(mv, depth);
        }
    }

    let node_type = if alpha > original_alpha {
        if alpha >= beta {
            NodeType::LowerBound
        } else {
            NodeType::Exact
        }
    } else {
        NodeType::UpperBound
    };

    tt.store(hash, depth as i8, alpha, best_move, node_type);

    (alpha, best_move)
}

pub fn search(
    board: &mut Board,
    tables: &MagicTables,
    depth: i32,
    ply: usize,
) -> (i32, Option<Move>) {
    let mut ctx = SearchContext::new();
    let mut tt = TranspositionTable::new(1 << 20);
    alpha_beta(
        board,
        tables,
        &mut ctx,
        &mut tt,
        depth,
        ply,
        i32::MIN + 1,
        i32::MAX,
    )
}
