use crate::board::Board;
use crate::moves::execute::{generate_captures, generate_legal, make_move_basic, undo_move_basic};
use crate::moves::magic::MagicTables;
use crate::moves::square_control::in_check;
use crate::moves::types::Move;
use crate::search::context::SearchContext;
use crate::search::eval::static_eval;
use crate::search::ordering::{mvv_lva_score, order_moves};
use crate::search::tt::{NodeType, TranspositionTable};

const MATE_SCORE: i32 = 100000;
const MATE_THRESHOLD: i32 = 99000; // Scores above this are mate scores

/// Adjust mate score when storing to TT (convert from search ply to TT ply)
#[inline]
fn score_to_tt(score: i32, ply: usize) -> i32 {
    if score > MATE_THRESHOLD {
        score + ply as i32
    } else if score < -MATE_THRESHOLD {
        score - ply as i32
    } else {
        score
    }
}

/// Adjust mate score when retrieving from TT (convert from TT ply to search ply)
#[inline]
fn score_from_tt(score: i32, ply: usize) -> i32 {
    if score > MATE_THRESHOLD {
        score - ply as i32
    } else if score < -MATE_THRESHOLD {
        score + ply as i32
    } else {
        score
    }
}

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
            return (if maximizing { -MATE_SCORE } else { MATE_SCORE }, None);
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

pub fn quiescence(
    board: &mut Board,
    tables: &MagicTables,
    ctx: &mut SearchContext,
    tt: &mut TranspositionTable,
    ply: usize,
    mut alpha: i32,
    beta: i32,
) -> i32 {
    let in_check_now = in_check(board, board.side_to_move, tables);

    if in_check_now {
        // eprintln!("IN CHECK! Searching all evasions");
        let mut moves = Vec::with_capacity(128);
        let mut scratch = Vec::with_capacity(128);
        generate_legal(board, tables, &mut moves, &mut scratch);

        // No legal moves = checkmate
        if moves.is_empty() {
            return -MATE_SCORE + ply as i32;
        }

        let mut alpha = alpha;
        for mv in moves {
            let undo = make_move_basic(board, mv);
            let score = -quiescence(board, tables, ctx, tt, ply + 1, -beta, -alpha);
            undo_move_basic(board, undo);

            if score >= beta {
                return beta;
            }
            if score > alpha {
                alpha = score;
            }
        }
        return alpha;
    }

    // Current evaluation
    let stand_pat = static_eval(board);

    // eprintln!(
    //     "Qsearch: stand_pat={}, alpha={}, beta={}",
    //     stand_pat, alpha, beta
    // );

    // Beta-cutoff
    if stand_pat >= beta {
        // eprintln!("  -> beta cutoff");
        return beta;
    }

    // Alpha update
    if stand_pat >= alpha {
        alpha = stand_pat;
    }

    // Generate only captures (and optionally checks)
    let mut moves = Vec::with_capacity(128);
    let mut scratch = Vec::with_capacity(128);
    generate_captures(board, tables, &mut moves, &mut scratch);

    // Order captures by MVV-LVA
    moves.sort_by_cached_key(|&mv| -mvv_lva_score(mv, board));

    for mv in moves {
        let mut captured_value = 0;
        // Getting just the piece and its attacker value
        if let Some(piece) = board.piece_type_at(mv.to) {
            captured_value = piece.value();
        }

        if stand_pat + captured_value + 200 < alpha {
            continue;
        }

        // Make and undo a move, test with quiescence
        let undo = make_move_basic(board, mv);
        let score = -quiescence(board, tables, ctx, tt, ply + 1, -beta, -alpha);
        undo_move_basic(board, undo);

        // Beta cutoff
        if score >= beta {
            return beta;
        }

        // Alpha update
        if score > alpha {
            alpha = score;
        }
    }
    alpha
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
            let tt_score = score_from_tt(entry.score, ply);
            match entry.node_type {
                NodeType::Exact => return (tt_score, entry.best_move),
                NodeType::LowerBound if tt_score >= beta => return (tt_score, entry.best_move),
                NodeType::UpperBound if tt_score <= alpha => return (tt_score, entry.best_move),
                _ => {}
            }
        }
    }

    if depth == 0 {
        let score = quiescence(board, tables, ctx, tt, ply, alpha, beta);
        return (score, None);
    }

    let mut moves = Vec::with_capacity(128);
    let mut scratch = Vec::with_capacity(128);

    generate_legal(board, tables, &mut moves, &mut scratch);
    order_moves(&mut moves, board, &ctx.killer_moves[ply], &ctx.history);

    if moves.is_empty() {
        if in_check(board, board.side_to_move, tables) {
            // Checkmate - we are mated
            // Use ply (distance from root), not depth (remaining depth)
            // Closer mate is worse, so more negative
            return (-MATE_SCORE + ply as i32, None);
        }

        // Stalemate
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

    let node_type = if alpha >= beta {
        NodeType::LowerBound
    } else if alpha > original_alpha {
        NodeType::Exact
    } else {
        NodeType::UpperBound
    };

    // Store score adjusted for TT
    let tt_score = score_to_tt(alpha, ply);
    tt.store(hash, depth as i8, tt_score, best_move, node_type);

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
