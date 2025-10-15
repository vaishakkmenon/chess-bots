use crate::board::{Board, Piece};
use crate::hash::zobrist::ep_file_to_hash;
use crate::moves::execute::{generate_captures, generate_legal, make_move_basic, undo_move_basic};
use crate::moves::magic::MagicTables;
use crate::moves::square_control::in_check;
use crate::moves::types::Move;
use crate::search::context::SearchContext;
use crate::search::eval::static_eval;
use crate::search::move_ordering::{mvv_lva_score, score_move};
use crate::search::tt::{NodeType, TranspositionTable};

pub const MATE: i32 = 30_000;
pub const INFTY: i32 = MATE + 2_000;
const MAX_PLY: i32 = 100;
const ASPIRATION_WINDOW: i32 = 50;

/// Helper Functions

/// Identify if the score is a checkmate
#[inline]
pub fn is_mate_score(score: i32) -> bool {
    score.abs() > MATE - MAX_PLY
}

/// Detect if position is in endgame (for null move pruning)
/// Returns true if:
/// - Side has only king + pawns, OR
/// - Total material < 1300 centipawns
#[inline]
fn is_endgame(board: &Board) -> bool {
    // Material values (same as your evaluation)
    const PAWN_VALUE: i32 = 100;
    const KNIGHT_VALUE: i32 = 320;
    const BISHOP_VALUE: i32 = 330;
    const ROOK_VALUE: i32 = 500;
    const QUEEN_VALUE: i32 = 900;

    let side = board.side_to_move;

    // Count pieces for the side to move
    let knights = board.pieces(Piece::Knight, side).count_ones();
    let bishops = board.pieces(Piece::Bishop, side).count_ones();
    let rooks = board.pieces(Piece::Rook, side).count_ones();
    let queens = board.pieces(Piece::Queen, side).count_ones();

    // Check if only king + pawns (no minor or major pieces)
    let only_king_and_pawns = knights == 0 && bishops == 0 && rooks == 0 && queens == 0;

    if only_king_and_pawns {
        return true;
    }

    // Calculate total material for side to move
    let pawns = board.pieces(Piece::Pawn, side).count_ones();

    let material = (pawns * PAWN_VALUE as u32)
        + (knights * KNIGHT_VALUE as u32)
        + (bishops * BISHOP_VALUE as u32)
        + (rooks * ROOK_VALUE as u32)
        + (queens * QUEEN_VALUE as u32);

    // Endgame if total material < 1300
    material < 1300
}

/// Quiescence search - searches only captures until position is quiet
fn quiesce(
    board: &mut Board,
    tables: &MagicTables,
    mut alpha: i32,
    beta: i32,
    ctx: &mut SearchContext,
    scratch: &mut Vec<Move>,
    ply: i32, // Track depth to prevent infinite loops
) -> i32 {
    const MAX_QUIESCE_PLY: i32 = 16; // Safety limit

    // Prevent infinite quiescence
    if ply > MAX_QUIESCE_PLY {
        return static_eval(board);
    }

    // Stand pat: current position evaluation
    let stand_pat = static_eval(board);

    // Beta cutoff - position is already too good for opponent
    if stand_pat >= beta {
        return beta;
    }

    // Update alpha - we can always "stand pat" and not capture
    if stand_pat > alpha {
        alpha = stand_pat;
    }

    // Generate and sort captures
    let mut pseudo_scratch = Vec::with_capacity(256);
    scratch.clear();
    generate_captures(board, tables, scratch, &mut pseudo_scratch);

    // Sort by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
    scratch.sort_unstable_by_key(|mv| -mvv_lva_score(mv, board));

    // Make a copy to avoid borrow issues
    let captures: Vec<Move> = scratch.clone();

    // Search each capture
    for &mv in captures.iter() {
        // Delta pruning (optional but recommended)
        const QUEEN_VALUE: i32 = 900;
        if stand_pat + mvv_lva_score(&mv, board) + QUEEN_VALUE < alpha {
            continue; // Even best case won't beat alpha
        }

        // Try the capture
        let undo = make_move_basic(board, mv);
        let score = -quiesce(board, tables, -beta, -alpha, ctx, scratch, ply + 1);
        undo_move_basic(board, undo);

        // Beta cutoff
        if score >= beta {
            return beta;
        }

        // Update best score
        if score > alpha {
            alpha = score;
        }
    }

    alpha
}

fn negamax(
    board: &mut Board,
    tables: &MagicTables,
    depth: i32,
    alpha: i32,
    beta: i32,
    ply: usize,
    ctx: &mut SearchContext,
    scratch: &mut Vec<Move>,
    tt: &mut TranspositionTable,
    allow_null_move: bool,
) -> i32 {
    // DON'T capture hash here - use board.zobrist directly throughout
    let probe_result = tt.probe(board.zobrist, depth, alpha, beta, ply as i32);

    // If we got a score cutoff, return it immediately
    if let Some(tt_score) = probe_result.score {
        return tt_score;
    }

    // Save the TT move for move ordering (even if no cutoff)
    let tt_move = probe_result.best_move;

    let original_alpha = alpha;

    // Draw detection first
    if board.halfmove_clock >= 100 || board.repetition_count() >= 3 {
        return 0; // draw
    }

    let in_check_now = in_check(board, board.side_to_move, tables);

    // Null Move Pruning
    // Null Move Pruning
    if allow_null_move && !in_check_now && depth >= 3 && !is_endgame(board) {
        const R: i32 = 2;

        let old_side = board.side_to_move;
        let old_ep = board.en_passant; // ← Save EP

        use crate::hash::zobrist::zobrist_keys;
        let keys = zobrist_keys();

        // XOR out old EP if it exists
        if let Some(f) = ep_file_to_hash(board) {
            board.zobrist ^= keys.ep_file[f as usize];
        }

        board.side_to_move = old_side.opposite();
        board.en_passant = None; // ← Clear EP for null move
        board.zobrist ^= keys.side_to_move;

        // Search with reduced depth and disallow another null move
        let null_score = -negamax(
            board,
            tables,
            depth - 1 - R,
            -beta,
            -beta + 1,
            ply + 1,
            ctx,
            scratch,
            tt,
            false,
        );

        // Restore
        board.side_to_move = old_side;
        board.en_passant = old_ep; // ← Restore EP
        board.zobrist ^= keys.side_to_move;

        // XOR in restored EP if it exists
        if let Some(f) = ep_file_to_hash(board) {
            board.zobrist ^= keys.ep_file[f as usize];
        }

        if null_score >= beta {
            return beta;
        }
    }

    // Generate legal moves ONCE
    let mut pseudo_scratch = Vec::with_capacity(256);
    scratch.clear();
    generate_legal(board, tables, scratch, &mut pseudo_scratch);

    // Terminal check
    if scratch.is_empty() {
        if in_check_now {
            return -(MATE - ply as i32);
        }
        return 0; // stalemate
    }

    // Base case
    if depth <= 0 {
        return quiesce(board, tables, alpha, beta, ctx, scratch, 0);
    }

    // Sort moves by score (descending = best first)
    scratch.sort_unstable_by_key(|mv| -score_move(mv, board, ctx, ply, tt_move));

    // Copy moves locally since scratch will be reused in recursion
    let legal_moves: Vec<Move> = scratch.clone();

    let mut a = alpha;
    let mut best_move = None;

    for (move_index, &mv) in legal_moves.iter().enumerate() {
        let undo = make_move_basic(board, mv);

        let gives_check = in_check(board, board.side_to_move, tables);

        // Check if this is a killer move
        let is_killer = ctx.is_killer(ply, mv);

        let mut score;

        let is_tt_move = tt_move.is_some() && tt_move == Some(mv);

        let can_reduce = move_index >= 4
            && depth >= 3
            && !in_check_now
            && !gives_check
            && !mv.is_capture()
            && !is_killer
            && !is_tt_move;

        if can_reduce {
            #[cfg(feature = "lmr_stats")]
            {
                ctx.lmr_reductions = ctx.lmr_reductions.saturating_add(1);
            }
            let reduction = if move_index >= 10 && depth >= 5 {
                2 // Aggressive for very late moves at high depth
            } else {
                1 // Conservative otherwise
            };

            let reduced_depth = (depth - 1 - reduction).max(0);

            score = -negamax(
                board,
                tables,
                reduced_depth,
                -beta,
                -a,
                ply + 1,
                ctx,
                scratch,
                tt,
                true,
            );

            // Re-search if promising
            if score > a {
                #[cfg(feature = "lmr_stats")]
                {
                    ctx.lmr_researches = ctx.lmr_researches.saturating_add(1);
                }
                score = -negamax(
                    board,
                    tables,
                    depth - 1,
                    -beta,
                    -a,
                    ply + 1,
                    ctx,
                    scratch,
                    tt,
                    true,
                );
            }
        } else {
            // Full depth search
            score = -negamax(
                board,
                tables,
                depth - 1,
                -beta,
                -a,
                ply + 1,
                ctx,
                scratch,
                tt,
                true,
            );
        }
        undo_move_basic(board, undo);

        if score > a {
            a = score;
            best_move = Some(mv);

            if a >= beta {
                // Beta cutoff!
                if !mv.is_capture() {
                    ctx.update_killer(ply, mv);
                    ctx.update_history(mv.piece, mv.to, depth);
                }

                // Store in TT - use board.zobrist directly (it's current and correct)
                tt.store(
                    board.zobrist,
                    depth,
                    a,
                    best_move,
                    NodeType::LowerBound,
                    ply as i32,
                );
                return a;
            }
        }
    }

    let node_type = if a >= beta {
        NodeType::LowerBound
    } else if a <= original_alpha {
        NodeType::UpperBound
    } else {
        NodeType::Exact
    };

    // Store in TT - use board.zobrist directly (it's current and correct)
    tt.store(board.zobrist, depth, a, best_move, node_type, ply as i32);

    a
}

pub fn search_fixed_depth(
    board: &mut Board,
    tables: &MagicTables,
    depth: i32,
    tt: &mut TranspositionTable,
    ctx: &mut SearchContext,
    alpha: i32,
    beta: i32,
) -> (i32, Option<Move>) {
    debug_assert!(depth >= 0);

    let mut scratch = Vec::with_capacity(256);
    let mut pseudo_scratch = Vec::with_capacity(256);

    let hash = board.zobrist;
    let root_probe = tt.probe(hash, depth, alpha, beta, 0);
    let root_tt_move = root_probe.best_move;
    ctx.clear_history();

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
    scratch.sort_unstable_by_key(|mv| -score_move(mv, board, &ctx, 0, root_tt_move));

    let root_moves = scratch.clone();
    let mut best_score = -INFTY;
    let mut best_move = None;
    let mut a = alpha;

    // Search each root move
    for &mv in root_moves.iter() {
        let undo = make_move_basic(board, mv);

        // Search with negated window (opponent's perspective)
        let score = -negamax(
            board,
            tables,
            depth - 1,
            -beta,
            -a,
            1,
            ctx,
            &mut scratch,
            tt,
            true,
        );

        undo_move_basic(board, undo);

        // Track best move
        if score > best_score {
            best_score = score;
            best_move = Some(mv);
        }

        if score > a {
            a = score;
        }

        if score >= beta {
            break;
        }
    }

    (best_score, best_move)
}

pub fn search_iterative_deepening(
    board: &mut Board,
    tables: &MagicTables,
    max_depth: i32,
) -> (i32, Option<Move>) {
    let mut ctx = SearchContext::new();
    let mut tt = TranspositionTable::new(64);

    let mut best_score = 0;
    let mut best_move = None;
    let mut prev_score = 0;

    tt.new_search();

    for depth in 1..=max_depth {
        #[cfg(feature = "lmr_stats")]
        ctx.reset_lmr_stats();
        let (mut score, mut mv);
        if depth == 1 {
            // Depth 1: No previous score, use full window
            (score, mv) =
                search_fixed_depth(board, tables, depth, &mut tt, &mut ctx, -INFTY, INFTY);
        } else {
            // Depth 2+: Use aspiration window around previous score
            let mut alpha = prev_score - ASPIRATION_WINDOW;
            let mut beta = prev_score + ASPIRATION_WINDOW;

            // Initial aspiration search
            (score, mv) = search_fixed_depth(board, tables, depth, &mut tt, &mut ctx, alpha, beta);

            // ← NEW: Handle fail-low (score <= alpha)
            if score <= alpha {
                // Score is worse than expected - widen window downward
                #[cfg(feature = "aspiration_stats")]
                {
                    ctx.aspiration_fails_low += 1;
                }
                alpha = -INFTY;
                (score, mv) =
                    search_fixed_depth(board, tables, depth, &mut tt, &mut ctx, alpha, beta);
            }

            // ← NEW: Handle fail-high (score >= beta)
            if score >= beta {
                // Score is better than expected - widen window upward
                #[cfg(feature = "aspiration_stats")]
                {
                    ctx.aspiration_fails_high += 1;
                }
                beta = INFTY;
                (score, mv) =
                    search_fixed_depth(board, tables, depth, &mut tt, &mut ctx, alpha, beta);
            }
        }

        best_score = score;
        prev_score = score;

        if let Some(m) = mv {
            best_move = Some(m);
            println!("info depth {} score cp {} pv {:?}", depth, score, m);
        } else {
            println!("info depth {} score cp {} pv (none)", depth, score);
        }

        #[cfg(feature = "lmr_stats")]
        {
            let r = ctx.lmr_reductions;
            let m = ctx.lmr_researches;
            let pct = if r > 0 {
                (m as f64 / r as f64) * 100.0
            } else {
                0.0
            };
            eprintln!("LMR: reductions={} re-searches={} ({:.1}%)", r, m, pct);
        }

        #[cfg(feature = "aspiration_stats")]
        {
            eprintln!(
                "Aspiration: fails_low={} fails_high={}",
                ctx.aspiration_fails_low, ctx.aspiration_fails_high
            );
        }
    }

    (best_score, best_move)
}
