use crate::board::Board;
use crate::moves::execute::{make_move_basic, make_null_move, undo_move_basic, undo_null_move};
use crate::moves::magic::MagicTables;
use crate::moves::square_control::in_check;
use crate::moves::types::Move;
use crate::search::context::SearchContext;
use crate::search::eval::static_eval;
use crate::search::picker::MovePicker;
use crate::search::see::SeeExt;
use crate::search::tt::{NodeType, TranspositionTable};
use std::time::{Duration, Instant};

const MATE_SCORE: i32 = 31000;
const MATE_THRESHOLD: i32 = 30000;
const INF: i32 = 32000;
const MAX_Q_SEARCH_DEPTH: usize = 100;

// --- TT Score Adjustment Helpers ---
fn score_to_tt(score: i32, ply: i32) -> i32 {
    if score >= MATE_THRESHOLD {
        score + ply
    } else if score <= -MATE_THRESHOLD {
        score - ply
    } else {
        score
    }
}

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

        if let Some(limit) = self.allotted {
            let elapsed = self.start_time.elapsed();

            // Hard Stop: Abort immediately if we hit the limit
            if elapsed >= limit {
                self.stop_signal = true;
            }
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
    nodes: &mut u64,
    time: &mut TimeManager,
) -> i32 {
    // SAFETY BRAKE: Prevent Q-search explosions
    if ply > MAX_Q_SEARCH_DEPTH {
        return static_eval(board, tables, alpha, beta);
    }

    let stand_pat = static_eval(board, tables, alpha, beta);

    if stand_pat >= beta {
        return beta;
    }
    if stand_pat >= alpha {
        alpha = stand_pat;
    }

    // Use MovePicker in captures-only mode for quiescence
    let empty_killers = [None, None];
    let empty_history = [[0i32; 64]; 64];
    let mut picker = MovePicker::new(None, empty_killers, true);

    while let Some(mv) = picker.next(board, tables, &empty_history) {
        *nodes += 1;
        if *nodes & 1023 == 0 {
            time.check_time();
        }
        if time.stop_signal {
            return stand_pat;
        }

        let mut captured_value = 0;
        if let Some(piece) = board.piece_type_at(mv.to) {
            captured_value = piece.value();
        }

        // DELTA PRUNING SAFETY
        // Don't prune if it's a promotion (potentially huge value)
        // Don't prune if it's En Passant (captured_value is 0, but it captures a pawn)
        let is_prom = mv.is_promotion();
        let is_ep = mv.is_en_passant();

        // "Blindness" Fix: Only prune standard captures.
        if !is_prom && !is_ep && stand_pat + captured_value + 200 < alpha {
            continue;
        }

        // SEE Pruning: Skip captures that lose material
        // Note: MovePicker already filters bad captures for us, but we keep this
        // for promotions and en passant which bypass SEE classification
        if !is_prom && !is_ep && !board.static_exchange_eval(mv, 0, tables) {
            continue;
        }

        let undo = make_move_basic(board, mv);
        let score = -quiescence(board, tables, ctx, tt, ply + 1, -beta, -alpha, nodes, time);
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
    // Check every 1024 nodes instead of 2047 for tighter control
    if *nodes & 1023 == 0 {
        time.check_time();
    }

    if time.stop_signal {
        return (0, None);
    }
    *nodes += 1;

    // Repetition Detection
    if ply > 0 && board.is_repetition() {
        return (0, None);
    }

    if time.stop_signal {
        return (0, None);
    }

    let hash = board.zobrist;
    let mut hash_move = None;

    // TT PROBE WITH MATE SCORE ADJUSTMENT
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
    } else {
    }

    if depth <= 0 {
        let score = quiescence(board, tables, ctx, tt, ply, alpha, beta, nodes, time);
        return (score, None);
    }

    let in_check_now = in_check(board, board.side_to_move, tables);

    // FIX 6: CHECK EXTENSION
    // If we are in check, extend the search by 1 ply.
    // This resolves forced mates and prevents the horizon effect.
    let extension = if in_check_now { 1 } else { 0 };

    // [STEP 1] Calculate Eval Early
    // We lift this out so both RFP and SFP can share it.
    let static_eval_val = if !in_check_now {
        static_eval(board, tables, alpha, beta)
    } else {
        0 // Dummy value, we won't use it if in check
    };

    // [STEP 2] Update Reverse Futility Pruning (RFP) to use the variable
    if depth < 9 && !in_check_now && ply > 0 {
        let margin = 120 * depth;
        // Use the pre-calculated variable
        if static_eval_val - margin >= beta {
            return (beta, None);
        }
    }
    // =============================================================

    // NULL MOVE PRUNING DEPTH
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

    // Use MovePicker for staged move generation
    let mut picker = MovePicker::new(hash_move, ctx.killer_moves[ply], false);

    let mut best_move = None;
    let mut best_score = -INF;
    let original_alpha = alpha;
    let mut move_count = 0;

    while let Some(mv) = picker.next(board, tables, &ctx.history) {
        // [STEP 3] STANDARD FUTILITY PRUNING
        // Logic: If the move is quiet and our position is hopelessly below Alpha, skip it.
        if depth < 7 && !in_check_now && !mv.is_capture() && !mv.is_promotion() && move_count > 0 {
            // Margin: We assume a quiet move can improve our position by at most 150 * depth.
            // If eval + margin is still <= alpha, this move cannot possibly beat alpha.
            let margin = 150 * depth;
            if static_eval_val + margin <= alpha {
                continue; // PRUNE: Skip to next move
            }
        }

        // =========================================================
        // LATE MOVE PRUNING (LMP)
        // =========================================================
        // Logic: If we have searched many quiet moves and haven't found a
        // good one yet, it's highly unlikely the remaining (unsorted) moves
        // will be any better. Just cut them off.
        if depth < 14
            && !in_check_now
            && !mv.is_capture()
            && !mv.is_promotion()
            && alpha == original_alpha
        {
            let lmp_threshold = 3 + 4 * depth;
            if move_count > lmp_threshold as usize {
                break;
            }
        }
        // =========================================================

        let undo = make_move_basic(board, mv);
        let mut score;

        if move_count == 0 {
            let (val, _) = alpha_beta(
                board,
                tables,
                ctx,
                tt,
                depth - 1 + extension,
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

            // Only reduce if:
            // 1. We are deep enough (> 2)
            // 2. We have searched the first few moves (move_count > 3)
            // 3. It's a quiet move (not a capture/promotion)
            // 4. We are not in check (tactical danger)
            if depth > 2
                && move_count > 3
                && !mv.is_capture()
                && !mv.is_promotion()
                && !in_check_now
            {
                // Base reduction
                r = 1;

                // If we are at high depth, reduce more
                if depth > 6 {
                    r += 1;
                }

                // If this is a very late move, reduce even more
                if move_count > 8 {
                    r += 1;
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
                    depth - 1 + extension,
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
        move_count += 1;

        if time.stop_signal {
            return (0, None);
        }

        if score > best_score {
            best_score = score;
            if score > alpha {
                alpha = score;
                best_move = Some(mv);
            }
            if score >= beta {
                // TT SAVE WITH MATE SCORE ADJUSTMENT (LowerBound/Beta Cutoff)
                let tt_score = score_to_tt(beta, ply as i32);
                tt.save(
                    hash,
                    Some(mv),
                    tt_score,
                    depth as u8,
                    NodeType::LowerBound as u8,
                    ply as i32,
                );

                if !mv.is_capture() {
                    ctx.update_killer(ply, mv);

                    let bonus = depth * depth;
                    ctx.update_history(mv, bonus);
                }

                return (beta, Some(mv));
            }
        }
    }

    // No legal moves found - checkmate or stalemate
    if move_count == 0 {
        if in_check_now {
            return (-MATE_SCORE + ply as i32, None);
        }
        return (0, None);
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

    // TT SAVE WITH MATE SCORE ADJUSTMENT (Best Score)
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
    let mut last_completed_best_move = None;
    let mut last_completed_best_score = 0;
    let mut nodes = 0;
    let mut tt = TranspositionTable::new(512);
    let mut ctx = SearchContext::new();
    let mut time = TimeManager::new(time_limit);

    for depth in 1..=max_depth {
        for from in 0..64 {
            for to in 0..64 {
                ctx.history[from][to] /= 8;
            }
        }

        // --- Aspiration Window Logic ---
        let mut alpha = -INF;
        let mut beta = INF;
        let window = 50; // Window size (50cp)

        // Only apply aspiration windows at depth > 4 for stability
        if depth > 4 {
            alpha = last_completed_best_score - window;
            beta = last_completed_best_score + window;
        }

        let mut score;
        let mut mv;

        loop {
            // Perform the search with the current window
            let result = alpha_beta(
                board, tables, &mut ctx, &mut tt, depth, 0, alpha, beta, &mut nodes, &mut time,
            );

            score = result.0;
            mv = result.1;

            // If we ran out of time during the search, stop immediately
            if time.stop_signal {
                break;
            }

            // 1. Fail Low (Score <= Alpha): Position is worse than expected.
            // Widen window downwards to -INF (Fail-Soft approach).
            if score <= alpha {
                beta = (alpha + beta) / 2;
                alpha = -INF;
                continue;
            }

            // 2. Fail High (Score >= Beta): Position is better than expected.
            // Widen window upwards to INF (Fail-Soft approach).
            if score >= beta {
                alpha = (alpha + beta) / 2;
                beta = INF;
                continue;
            }

            // 3. Success: Score is within the window.
            break;
        }
        // -------------------------------

        // CRITICAL FIX: If the stop signal was triggered, DO NOT update the best move.
        // The search at this depth is incomplete and likely contains blunders.
        if time.stop_signal {
            break;
        }

        // Only update if the depth actually finished
        last_completed_best_score = score;
        last_completed_best_move = mv;

        // Output info for GUI (standard UCI)
        if let Some(valid_mv) = last_completed_best_move {
            let score_str = if last_completed_best_score.abs() >= MATE_THRESHOLD {
                let moves = (MATE_SCORE - last_completed_best_score.abs() + 1) / 2;
                if last_completed_best_score > 0 {
                    format!("mate {}", moves)
                } else {
                    format!("mate -{}", moves)
                }
            } else {
                format!("cp {}", last_completed_best_score)
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

        // Optimization: If we found a mate, stop searching deeper
        if score.abs() >= MATE_THRESHOLD {
            break;
        }
    }

    (last_completed_best_score, last_completed_best_move)
}
