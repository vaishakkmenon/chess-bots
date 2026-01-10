use crate::board::{Board, Color, Piece};
use crate::search::pesto;
use crate::utils::pop_lsb;

// Phase Weights
const KNIGHT_PHASE: i32 = 1;
const BISHOP_PHASE: i32 = 1;
const ROOK_PHASE: i32 = 2;
const QUEEN_PHASE: i32 = 4;
const TOTAL_PHASE: i32 = 24;

fn calculate_phase(board: &Board) -> i32 {
    let knights = board.pieces(Piece::Knight, Color::White).count_ones()
        + board.pieces(Piece::Knight, Color::Black).count_ones();
    let bishops = board.pieces(Piece::Bishop, Color::White).count_ones()
        + board.pieces(Piece::Bishop, Color::Black).count_ones();
    let rooks = board.pieces(Piece::Rook, Color::White).count_ones()
        + board.pieces(Piece::Rook, Color::Black).count_ones();
    let queens = board.pieces(Piece::Queen, Color::White).count_ones()
        + board.pieces(Piece::Queen, Color::Black).count_ones();

    let current_phase_material = (knights as i32 * KNIGHT_PHASE)
        + (bishops as i32 * BISHOP_PHASE)
        + (rooks as i32 * ROOK_PHASE)
        + (queens as i32 * QUEEN_PHASE);

    current_phase_material.min(TOTAL_PHASE).max(0)
}

#[inline(always)]
pub fn mirror_vert(sq: u8) -> usize {
    (sq ^ 56) as usize
}

// Helper: Map piece to tables from pesto.rs
fn get_psqt(kind: Piece) -> (&'static [i32; 64], &'static [i32; 64]) {
    match kind {
        Piece::Pawn => (&pesto::PAWN_TABLE.0, &pesto::PAWN_TABLE.1),
        Piece::Knight => (&pesto::KNIGHT_TABLE.0, &pesto::KNIGHT_TABLE.1),
        Piece::Bishop => (&pesto::BISHOP_TABLE.0, &pesto::BISHOP_TABLE.1),
        Piece::Rook => (&pesto::ROOK_TABLE.0, &pesto::ROOK_TABLE.1),
        Piece::Queen => (&pesto::QUEEN_TABLE.0, &pesto::QUEEN_TABLE.1),
        Piece::King => (&pesto::KING_TABLE.0, &pesto::KING_TABLE.1),
    }
}

// Helper: Map piece to material values
fn get_piece_value(kind: Piece) -> (i32, i32) {
    match kind {
        Piece::Pawn => pesto::PAWN_VAL,
        Piece::Knight => pesto::KNIGHT_VAL,
        Piece::Bishop => pesto::BISHOP_VAL,
        Piece::Rook => pesto::ROOK_VAL,
        Piece::Queen => pesto::QUEEN_VAL,
        Piece::King => pesto::KING_VAL,
    }
}

pub fn evaluate(board: &Board) -> i32 {
    let mut mg_score = 0;
    let mut eg_score = 0;
    let phase = calculate_phase(board);

    // Iterate over all piece types
    // Note: Iterate over colors for efficiency if needed, but per piece type is fine
    for piece_type in [
        Piece::Pawn,
        Piece::Knight,
        Piece::Bishop,
        Piece::Rook,
        Piece::Queen,
        Piece::King,
    ] {
        let (mg_val, eg_val) = get_piece_value(piece_type);
        let (mg_table, eg_table) = get_psqt(piece_type);

        // White pieces
        let mut w_bb = board.pieces(piece_type, Color::White);
        while w_bb != 0 {
            let sq = pop_lsb(&mut w_bb);
            // White is at bottom, normal index
            mg_score += mg_val + mg_table[sq as usize];
            eg_score += eg_val + eg_table[sq as usize];
        }

        // Black pieces
        let mut b_bb = board.pieces(piece_type, Color::Black);
        while b_bb != 0 {
            let sq = pop_lsb(&mut b_bb);
            // Black is at top, mirror index
            let mirrored_sq = mirror_vert(sq);
            mg_score -= mg_val + mg_table[mirrored_sq];
            eg_score -= eg_val + eg_table[mirrored_sq];
        }
    }

    // Tapered Formula
    // Score = (MG * Phase + EG * (24 - Phase)) / 24
    let score = (mg_score * phase + eg_score * (TOTAL_PHASE - phase)) / TOTAL_PHASE;

    // Return score relative to side to move
    if board.side_to_move == Color::White {
        score
    } else {
        -score
    }
}

// Compatibility wrapper if older code calls static_eval
pub fn static_eval(board: &Board) -> i32 {
    evaluate(board)
}

// Debug helper: returns just the material component (tapered)
pub fn eval_material(board: &Board) -> i32 {
    let mut mg_score = 0;
    let mut eg_score = 0;
    let phase = calculate_phase(board);

    for piece_type in [
        Piece::Pawn,
        Piece::Knight,
        Piece::Bishop,
        Piece::Rook,
        Piece::Queen,
        Piece::King,
    ] {
        let (mg_val, eg_val) = get_piece_value(piece_type);

        let w_count = board.pieces(piece_type, Color::White).count_ones() as i32;
        let b_count = board.pieces(piece_type, Color::Black).count_ones() as i32;

        mg_score += mg_val * (w_count - b_count);
        eg_score += eg_val * (w_count - b_count);
    }

    (mg_score * phase + eg_score * (TOTAL_PHASE - phase)) / TOTAL_PHASE
}

// Debug helper: returns just the PSQT component (tapered)
pub fn eval_psqt(board: &Board) -> i32 {
    let mut mg_score = 0;
    let mut eg_score = 0;
    let phase = calculate_phase(board);

    for piece_type in [
        Piece::Pawn,
        Piece::Knight,
        Piece::Bishop,
        Piece::Rook,
        Piece::Queen,
        Piece::King,
    ] {
        let (mg_table, eg_table) = get_psqt(piece_type);

        let mut w_bb = board.pieces(piece_type, Color::White);
        while w_bb != 0 {
            let sq = pop_lsb(&mut w_bb);
            mg_score += mg_table[sq as usize];
            eg_score += eg_table[sq as usize];
        }

        let mut b_bb = board.pieces(piece_type, Color::Black);
        while b_bb != 0 {
            let sq = pop_lsb(&mut b_bb);
            let mirrored_sq = mirror_vert(sq);
            mg_score -= mg_table[mirrored_sq];
            eg_score -= eg_table[mirrored_sq];
        }
    }

    (mg_score * phase + eg_score * (TOTAL_PHASE - phase)) / TOTAL_PHASE
}
