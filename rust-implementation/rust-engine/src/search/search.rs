use crate::board::{Board, Color};
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

const MATE_SCORE: i32 = 100000;
const MATE_THRESHOLD: i32 = 99000; // Scores above this are mate scores
const INF: i32 = 1_000_000;

/// Adjust mate score when storing to TT (convert from search ply to TT ply)
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

        // No legal moves = checkmate or stalemate
        if moves.is_empty() {
            // If in check and no legal moves, it's checkmate
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
    //     "Qsearch ply {}: stand_pat={}, stm={:?}",
    //     ply, stand_pat, board.side_to_move
    // );

    // Beta-cutoff
    if stand_pat >= beta {
        return beta;
    }

    // Alpha update
    if stand_pat >= alpha {
        alpha = stand_pat;
    }

    // Generate captures and checks
    let mut moves = Vec::with_capacity(128);
    let mut scratch = Vec::with_capacity(128);
    generate_captures(board, tables, &mut moves, &mut scratch);

    // Order captures by MVV-LVA
    moves.sort_by_cached_key(|&mv| -mvv_lva_score(mv, board));

    for mv in moves {
        let mut captured_value = 0;
        // Getting just the piece and its value
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
    // 1. Periodic Time Check (every 2048 nodes)
    *nodes += 1;
    if (*nodes).is_multiple_of(2048) {
        time.check_time();
    }

    // 2. Immediate Abort if time is up
    if time.stop_signal {
        return (0, None); // Return dummy value
    }

    let hash = board.zobrist;
    let mut hash_move = None;

    // Probe TT
    if let Some(entry) = tt.probe(hash) {
        hash_move = entry.best_move;

        if entry.depth >= depth as i8 {
            let mut tt_score = score_from_tt(entry.score, ply);

            if board.side_to_move == Color::Black {
                tt_score = -tt_score;
            }

            match entry.node_type {
                NodeType::Exact => {
                    return (tt_score, entry.best_move);
                }
                NodeType::LowerBound if tt_score >= beta => {
                    return (tt_score, entry.best_move);
                }
                NodeType::UpperBound if tt_score <= alpha => {
                    return (tt_score, entry.best_move);
                }
                _ => {}
            }
        }
    }

    if depth <= 0 {
        let score = quiescence(board, tables, ctx, tt, ply, alpha, beta);
        return (score, None);
    }

    // Null Move Pruning
    // Only attempt if depth is high enough, we are not in a PV node (beta-alpha == 1),
    // and we have major pieces (to avoid Zugzwang).
    // Also, we must not be in check (NMP acts as a "pass", valid only if no thread exists).
    let in_check_now = in_check(board, board.side_to_move, tables);

    if depth >= 3
        && !in_check_now
        && (beta - alpha == 1)
        && board.has_major_pieces(board.side_to_move)
    {
        let r = 2;
        let undo = make_null_move(board);

        let (score, _) = alpha_beta(
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
        let score = -score;
        undo_null_move(board, undo);

        if score >= beta {
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

    for (i, mv) in moves.into_iter().enumerate() {
        let undo = make_move_basic(board, mv);
        let mut score;

        // --- PVS LOGIC START ---

        if i == 0 {
            // 1. PV Move: Full Window, Full Depth
            // We trust the first move (from TT or sorting) is best.
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
            // 2. Late Moves: Try to prove they are worse using Null Window

            // A. Calculate LMR
            let mut r = 0;
            // Conditions: index >= 4, depth >= 3, not capture/promo, not in check
            // Note: We use 'i >= 4' which means the 5th move (indexes 0,1,2,3 are top 4).
            if depth >= 3 && i >= 4 && !mv.is_capture() && !mv.is_promotion() && !in_check_now {
                // Aggressive LMR used: R=2 if d>=6 & i>=10, else R=1
                if depth >= 6 && i >= 10 {
                    r = 2;
                } else {
                    r = 1;
                }
            }

            // B. Scout Search (LMR + Zero Window)
            // We search with [-alpha-1, -alpha] to prove fail-low
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

            // C. LMR Recovery
            // If we reduced (r > 0) but the move beat alpha, our reduction was wrong.
            // We must re-search at full depth (but still Zero Window to save time).
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

            // D. PVS Re-Search (Full Window)
            // If the move is better than alpha (and didn't cause a beta cutoff),
            // it means it's a NEW best move. We need the exact score.
            // Also ensure we don't re-search if score >= beta (that's a cutoff!)
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
        // --- PVS LOGIC END ---

        undo_move_basic(board, undo);

        if score >= beta {
            // Beta cutoff - store LowerBound entry before returning
            let white_score = if board.side_to_move == Color::White {
                beta
            } else {
                -beta
            };
            let tt_score = score_to_tt(white_score, ply);
            tt.store(hash, depth as i8, tt_score, Some(mv), NodeType::LowerBound);

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
    let white_score = if board.side_to_move == Color::White {
        alpha
    } else {
        -alpha
    };
    let tt_score = score_to_tt(white_score, ply);
    tt.store(hash, depth as i8, tt_score, best_move, node_type);

    (alpha, best_move)
}

pub fn search(
    board: &mut Board,
    tables: &MagicTables,
    max_depth: i32,
    time_limit: Option<Duration>,
) -> (i32, Option<Move>) {
    let mut best_move: Option<Move> = None;
    let mut best_score = 0;

    let mut ctx = SearchContext::new();
    // Keep the large TT size you just added
    let mut tt = TranspositionTable::new(1 << 24);
    let mut time = TimeManager::new(time_limit);
    let mut nodes = 0;

    for depth in 1..=max_depth {
        // Decay history heuristics to keep them fresh
        for from in 0..64 {
            for to in 0..64 {
                ctx.history[from][to] /= 8;
            }
        }

        // --- ASPIRATION WINDOW LOGIC START ---
        // Default: Infinite window for shallow depths
        let mut alpha = -INF;
        let mut beta = INF;
        let mut delta = 50; // Initial window size (50cp = 0.5 pawns)

        // Only use aspiration windows for deeper searches (Depth 5+)
        if depth >= 5 {
            alpha = (-MATE_SCORE).max(best_score - delta);
            beta = (MATE_SCORE).min(best_score + delta);
        }

        loop {
            let (score, mv) = alpha_beta(
                board, tables, &mut ctx, &mut tt, depth, 0, alpha, beta, &mut nodes, &mut time,
            );

            // Abort if time ran out
            if time.stop_signal {
                break;
            }

            // FAIL LOW: The score is worse than we expected (<= alpha)
            // The position is worse than we thought. We need to widen the window DOWN.
            if score <= alpha {
                alpha = (-INF).max(alpha - delta);
                delta += delta / 2; // Widen the window aggressively (exponentially)
                continue; // Re-search with new bounds
            }

            // FAIL HIGH: The score is better than we expected (>= beta)
            // The position is better than we thought. We need to widen the window UP.
            if score >= beta {
                beta = (INF).min(beta + delta);
                delta += delta / 2;
                continue; // Re-search with new bounds
            }

            // EXACT MATCH: The score is inside our window. We found the truth!
            best_score = score; // Always update score!

            if let Some(valid_mv) = mv {
                best_move = Some(valid_mv);
                println!(
                    "info depth {} score cp {} pv {}",
                    depth,
                    score,
                    valid_mv.to_uci()
                );
            }

            // If we found a mate (or were mated), stop searching deeper
            if score.abs() > MATE_THRESHOLD {
                break;
            }

            break; // Done with this depth
        }
        // --- ASPIRATION WINDOW LOGIC END ---

        if time.stop_signal {
            println!("info string Time up!");
            break;
        }

        // If found mate, break outer loop too
        if best_score.abs() > MATE_THRESHOLD {
            break;
        }
    }

    (best_score, best_move)
}
