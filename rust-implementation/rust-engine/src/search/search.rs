use crate::board::{Board, Piece};
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
    let hash = board.compute_zobrist_full();

    let probe_result = tt.probe(hash, depth, alpha, beta, ply as i32);

    // If we got a score cutoff, return it immediately
    if let Some(tt_score) = probe_result.score {
        return tt_score;
    }

    // Save the TT move for move ordering (even if no cutoff)
    let tt_move = probe_result.best_move;

    let original_alpha = alpha; // ← SAVE ORIGINAL ALPHA

    // Draw detection first
    if board.halfmove_clock >= 100 || board.repetition_count() >= 3 {
        return 0; // draw
    }

    // Null Move Pruning
    if allow_null_move
        && !in_check(board, board.side_to_move, tables)
        && depth >= 3
        && !is_endgame(board)
    {
        const R: i32 = 2; // Reduction factor (can tune this)

        // Make null move (just flip side to move)
        let old_side = board.side_to_move;
        board.side_to_move = old_side.opposite();

        use crate::hash::zobrist::zobrist_keys;
        let keys = zobrist_keys();
        board.zobrist ^= keys.side_to_move; // Update hash for side change

        // Search with reduced depth and disallow another null move
        let null_score = -negamax(
            board,
            tables,
            depth - 1 - R, // Reduced depth
            -beta,
            -beta + 1, // Null window
            ply + 1,
            ctx,
            scratch,
            tt,
            false, // ← IMPORTANT: Don't allow consecutive null moves
        );

        // Undo null move
        board.side_to_move = old_side;
        board.zobrist ^= keys.side_to_move; // Restore hash

        // If null move causes beta cutoff, position is too good
        if null_score >= beta {
            return beta; // Cutoff!
        }
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
    if depth <= 0 {
        return quiesce(board, tables, alpha, beta, ctx, scratch, 0);
    }

    // Sort moves by score (descending = best first)
    scratch.sort_unstable_by_key(|mv| -score_move(mv, board, ctx, ply, tt_move));

    // Copy moves locally since scratch will be reused in recursion
    let legal_moves: Vec<Move> = scratch.clone();

    let mut a = alpha;
    let mut best_move = None; // ← TRACK BEST MOVE

    for &mv in legal_moves.iter() {
        let undo = make_move_basic(board, mv);
        let score = -negamax(
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
        undo_move_basic(board, undo);

        if score > a {
            a = score;
            best_move = Some(mv); // ← UPDATE BEST MOVE

            if a >= beta {
                // Beta cutoff!
                if !mv.is_capture() {
                    ctx.update_killer(ply, mv);
                    ctx.update_history(mv.piece, mv.to, depth);
                }

                // ← STORE IN TT BEFORE RETURNING
                tt.store(hash, depth, a, best_move, NodeType::LowerBound, ply as i32);
                return a;
            }
        }
    }

    // ← DETERMINE NODE TYPE USING CORRECT VARIABLES
    let node_type = if a >= beta {
        NodeType::LowerBound
    } else if a <= original_alpha {
        NodeType::UpperBound
    } else {
        NodeType::Exact
    };

    tt.store(hash, depth, a, best_move, node_type, ply as i32);

    a
}

pub fn search_fixed_depth(
    board: &mut Board,
    tables: &MagicTables,
    depth: i32,
    tt: &mut TranspositionTable,
) -> (i32, Option<Move>) {
    debug_assert!(depth >= 0);

    let mut ctx = SearchContext::new();
    let mut scratch = Vec::with_capacity(256);
    let mut pseudo_scratch = Vec::with_capacity(256);

    let hash = board.compute_zobrist_full();
    let root_probe = tt.probe(hash, depth, -INFTY, INFTY, 0);
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
            tt,
            true,
        );

        undo_move_basic(board, undo);

        // Track best move
        if score > best_score {
            best_score = score;
            best_move = Some(mv);
        }
    }

    (best_score, best_move)
}

pub fn search_iterative_deepening(
    board: &mut Board,
    tables: &MagicTables,
    max_depth: i32,
) -> (i32, Option<Move>) {
    let mut tt = TranspositionTable::new(64);

    let mut best_score = 0;
    let mut best_move = None;

    tt.new_search();

    for depth in 1..=max_depth {
        let (score, mv) = search_fixed_depth(board, tables, depth, &mut tt);
        best_score = score;

        if let Some(m) = mv {
            best_move = Some(m);
            println!("info depth {} score cp {} pv {:?}", depth, score, m);
        } else {
            println!("info depth {} score cp {} pv (none)", depth, score);
        }
    }

    (best_score, best_move)
}
