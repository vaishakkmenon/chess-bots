use crate::board::Board;
use crate::moves::execute::{
    generate_captures, generate_legal, make_move_basic, make_null_move, undo_move_basic,
    undo_null_move,
};
use crate::moves::magic::MagicTables;
use crate::moves::square_control::in_check;
use crate::moves::types::Move;
use crate::search::context::SearchContext;
use crate::search::eval::static_eval;
use crate::search::ordering::{mvv_lva_score, order_moves};
use crate::search::tt::{NodeType, TranspositionTable};
use std::time::{Duration, Instant};

const MATE_SCORE: i32 = 31000;
const MATE_THRESHOLD: i32 = 30000;
const INF: i32 = 32000;

// --- TT Score Adjustment Helpers ---
// Converts a score relative to the current ply (search) to a score independent of ply (TT)
fn score_to_tt(score: i32, ply: i32) -> i32 {
    if score >= MATE_THRESHOLD {
        score + ply
    } else if score <= -MATE_THRESHOLD {
        score - ply
    } else {
        score
    }
}

// Converts a score from the TT (independent) back to relative to current ply (search)
fn score_from_tt(score: i32, ply: i32) -> i32 {
    if score >= MATE_THRESHOLD {
        score - ply
    } else if score <= -MATE_THRESHOLD {
        score + ply
    } else {
        score
    }
}
// -----------------------------------

pub struct TimeManager {
    pub start_time: Instant,
    pub allotted: Option<Duration>,
    pub stop_signal: bool,
}

impl TimeManager {
    pub fn new(limit: Option<Duration>) -> Self {
        Self {
            start_time: Instant::now(),
            allotted: limit,
            stop_signal: false,
        }
    }

    #[inline(always)]
    pub fn check_time(&mut self) {
        if self.stop_signal {
            return;
        }
        if let Some(limit) = self.allotted
            && self.start_time.elapsed() > limit
        {
            self.stop_signal = true;
        }
    }
}

#[allow(clippy::too_many_arguments, clippy::only_used_in_recursion)]
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
        let mut moves = Vec::with_capacity(128);
        let mut scratch = Vec::with_capacity(128);
        generate_legal(board, tables, &mut moves, &mut scratch);

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

    let stand_pat = static_eval(board, tables);

    if stand_pat >= beta {
        return beta;
    }
    if stand_pat >= alpha {
        alpha = stand_pat;
    }

    let mut moves = Vec::with_capacity(128);
    let mut scratch = Vec::with_capacity(128);
    generate_captures(board, tables, &mut moves, &mut scratch);
    moves.sort_by_cached_key(|&mv| -mvv_lva_score(mv, board));

    for mv in moves {
        let mut captured_value = 0;
        if let Some(piece) = board.piece_type_at(mv.to) {
            captured_value = piece.value();
        }

        // FIX 1: DELTA PRUNING SAFETY
        // Don't prune if it's a promotion (potentially huge value)
        // Don't prune if it's En Passant (captured_value is 0, but it captures a pawn)
        let is_prom = mv.is_promotion();
        let is_ep = mv.is_en_passant(); // Ensure your Move struct has this, or check move flags

        // "Blindness" Fix: Only prune standard captures.
        if !is_prom && !is_ep && stand_pat + captured_value + 200 < alpha {
            continue;
        }

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
    alpha
}

#[allow(clippy::too_many_arguments, clippy::only_used_in_recursion)]
pub fn alpha_beta(
    board: &mut Board,
    tables: &MagicTables,
    ctx: &mut SearchContext,
    tt: &mut TranspositionTable,
    depth: i32,
    ply: usize,
    mut alpha: i32,
    beta: i32,
    nodes: &mut u64,
    time: &mut TimeManager,
) -> (i32, Option<Move>) {
    if *nodes & 2047 == 0 {
        time.check_time();
    }
    *nodes += 1;

    if time.stop_signal {
        return (0, None);
    }

    let hash = board.zobrist;
    let mut hash_move = None;

    // FIX 2: TT PROBE WITH MATE SCORE ADJUSTMENT
    if let Some((tt_move, raw_score, tt_depth, tt_bound)) =
        tt.probe(hash, depth as u8, alpha, beta, ply as i32)
    {
        if let Some(tm) = tt_move {
            hash_move = Some(tm);
        }

        if tt_depth >= depth as u8 {
            // Convert the stored independent score back to relative score
            let tt_score = score_from_tt(raw_score, ply as i32);

            if ply > 0 {
                match tt_bound {
                    0 => return (tt_score, tt_move),
                    1 if tt_score >= beta => return (tt_score, tt_move),
                    2 if tt_score <= alpha => return (tt_score, tt_move),
                    _ => {}
                }
            }
        }
    }

    if depth <= 0 {
        let score = quiescence(board, tables, ctx, tt, ply, alpha, beta);
        return (score, None);
    }

    let in_check_now = in_check(board, board.side_to_move, tables);

    // =============================================================
    // REVERSE FUTILITY PRUNING (RFP)
    // =============================================================
    // Rule: "If I do nothing and I'm still winning by a lot, stop searching."
    // This safely prunes lines where we are crushing the opponent.
    if depth < 9 && !in_check_now && ply > 0 {
        let eval = static_eval(board, tables);

        // Margin: 120 per depth.
        // e.g., at Depth 1, we need to be up by 120. At Depth 5, up by 600.
        let margin = 120 * depth;

        if eval - margin >= beta {
            return (beta, None);
        }
    }
    // =============================================================

    // FIX 3: NULL MOVE PRUNING DEPTH
    // Increased from 3 to 4.
    // At depth 3, NMP reduces to depth 0 (Q-search). If there is a positional threat
    // that Q-search doesn't see (non-capture), the engine loses.
    // Depth 4 ensures we search at least depth 1 recursively, finding one layer of quiet moves.
    if depth >= 4
        && !in_check_now
        && (beta - alpha == 1)
        && board.has_major_pieces(board.side_to_move)
    {
        let r = 2;
        let undo = make_null_move(board);

        // Pass beta - 1 as alpha, beta as beta (Zero Window)
        let (val, _) = alpha_beta(
            board,
            tables,
            ctx,
            tt,
            depth - r - 1,
            ply + 1,
            -beta,
            -beta + 1,
            nodes,
            time,
        );
        let score = -val;
        undo_null_move(board, undo);

        if score >= beta && !time.stop_signal {
            // Don't save null move results to TT to avoid polluting standard search
            return (beta, None);
        }
    }

    let mut moves = Vec::with_capacity(128);
    let mut scratch = Vec::with_capacity(128);

    generate_legal(board, tables, &mut moves, &mut scratch);
    order_moves(
        &mut moves,
        board,
        &ctx.killer_moves[ply],
        &ctx.history,
        hash_move,
    );

    if moves.is_empty() {
        if in_check_now {
            return (-MATE_SCORE + ply as i32, None);
        }
        return (0, None);
    }

    let mut best_move = None;
    let mut best_score = -INF;
    let original_alpha = alpha;

    for (i, mv) in moves.into_iter().enumerate() {
        let undo = make_move_basic(board, mv);
        let mut score;

        if i == 0 {
            let (val, _) = alpha_beta(
                board,
                tables,
                ctx,
                tt,
                depth - 1,
                ply + 1,
                -beta,
                -alpha,
                nodes,
                time,
            );
            score = -val;
        } else {
            // LMR Logic
            let mut r = 0;
            // Condition 1: Base LMR (Reduce by 1)
            // Kept depth > 3 check for LMR (only reduces at depth 4+)
            if depth > 3 && i >= 4 && !mv.is_capture() && !mv.is_promotion() && !in_check_now {
                r = 1;

                // Condition 2: Aggressive LMR (Reduce by 2)
                // Pushing this to 8 ensures we don't blind ourselves too early.
                if depth >= 8 && i >= 10 {
                    r = 2;
                }
            }

            let (val, _) = alpha_beta(
                board,
                tables,
                ctx,
                tt,
                depth - 1 - r,
                ply + 1,
                -alpha - 1,
                -alpha,
                nodes,
                time,
            );
            score = -val;

            if r > 0 && score > alpha {
                let (val, _) = alpha_beta(
                    board,
                    tables,
                    ctx,
                    tt,
                    depth - 1,
                    ply + 1,
                    -alpha - 1,
                    -alpha,
                    nodes,
                    time,
                );
                score = -val;
            }

            if score > alpha && score < beta {
                let (val, _) = alpha_beta(
                    board,
                    tables,
                    ctx,
                    tt,
                    depth - 1,
                    ply + 1,
                    -beta,
                    -alpha,
                    nodes,
                    time,
                );
                score = -val;
            }
        }

        undo_move_basic(board, undo);

        if time.stop_signal {
            return (0, None);
        }

        if score > best_score {
            best_score = score;
            if score > alpha {
                alpha = score;
                best_move = Some(mv);
                ctx.update_history(mv, depth);
            }
            if score >= beta {
                // FIX 4: TT SAVE WITH MATE SCORE ADJUSTMENT (LowerBound/Beta Cutoff)
                let tt_score = score_to_tt(beta, ply as i32);
                tt.save(
                    hash,
                    Some(mv),
                    tt_score,
                    depth as u8,
                    NodeType::LowerBound as u8,
                    ply as i32,
                );

                ctx.update_killer(ply, mv);
                return (beta, Some(mv));
            }
        }
    }

    if time.stop_signal {
        return (0, None);
    }

    let node_type = if best_score >= beta {
        NodeType::LowerBound
    } else if best_score > original_alpha {
        NodeType::Exact
    } else {
        NodeType::UpperBound
    };

    // FIX 5: TT SAVE WITH MATE SCORE ADJUSTMENT (Best Score)
    // We save 'best_score' (which is alpha if exact, or the best failed low score if UpperBound)
    let tt_score = score_to_tt(best_score, ply as i32);
    tt.save(
        hash,
        best_move,
        tt_score,
        depth as u8,
        node_type as u8,
        ply as i32,
    );

    (best_score, best_move)
}

pub fn search(
    board: &mut Board,
    tables: &MagicTables,
    max_depth: i32,
    time_limit: Option<Duration>,
) -> (i32, Option<Move>) {
    let mut best_move = None;
    let mut best_score = 0;
    let mut nodes = 0;
    let mut tt = TranspositionTable::new(64);
    let mut ctx = SearchContext::new();
    let mut time = TimeManager::new(time_limit);

    for depth in 1..=max_depth {
        for from in 0..64 {
            for to in 0..64 {
                ctx.history[from][to] /= 8;
            }
        }

        let (score, mv) = alpha_beta(
            board, tables, &mut ctx, &mut tt, depth, 0, -INF, INF, &mut nodes, &mut time,
        );

        if time.stop_signal {
            println!("info string Time up! Aborting search at depth {}", depth);
            break;
        }

        best_score = score;
        if let Some(valid_mv) = mv {
            best_move = Some(valid_mv);

            // Output logic for GUI
            let score_str = if score.abs() >= MATE_THRESHOLD {
                let moves = (MATE_SCORE - score.abs() + 1) / 2;
                if score > 0 {
                    format!("mate {}", moves)
                } else {
                    format!("mate -{}", moves)
                }
            } else {
                format!("cp {}", score)
            };

            println!(
                "info depth {} score {} nodes {} time {} pv {}",
                depth,
                score_str,
                nodes,
                time.start_time.elapsed().as_millis(),
                valid_mv.to_uci()
            );
        }

        // Now MATE_THRESHOLD is actually functional for stopping search early
        if score.abs() >= MATE_THRESHOLD {
            break;
        }
    }

    (best_score, best_move)
}
