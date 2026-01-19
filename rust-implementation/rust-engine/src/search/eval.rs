use crate::board::{Board, Color, Piece};
use crate::moves::magic::MagicTables;
use crate::search::pesto;
use crate::square::Square;
use crate::utils::pop_lsb;

const MOBILITY_WEIGHT: i32 = 5;
const ISOLATED_PAWN_PENALTY: i32 = -15;
const DOUBLED_PAWN_PENALTY: i32 = -10;
const LAZY_EVAL_MARGIN: i32 = 200;
const KING_ZONE_ATTACK_PENALTY: i32 = 15;

#[allow(dead_code)]
const PASSED_PAWN_BONUS: [i32; 8] = [0, 0, 10, 20, 40, 70, 120, 0];

// Phase Weights
const KNIGHT_PHASE: i32 = 1;
const BISHOP_PHASE: i32 = 1;
const ROOK_PHASE: i32 = 2;
const QUEEN_PHASE: i32 = 4;
const TOTAL_PHASE: i32 = 24;

// --- Helper: Bitboard Iteration ---
// Iterates through squares in a bitboard (Least Significant Bit first)
struct BitIter(u64);
impl Iterator for BitIter {
    type Item = usize;
    fn next(&mut self) -> Option<Self::Item> {
        if self.0 == 0 {
            None
        } else {
            let lsb = self.0.trailing_zeros();
            self.0 &= self.0 - 1; // Clear LSB
            Some(lsb as usize)
        }
    }
}

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

pub fn static_eval(board: &Board, tables: &MagicTables, alpha: i32, beta: i32) -> i32 {
    let side = board.side_to_move;
    let enemy = side.opposite();

    // 1. Perspective Base Score
    let color_multiplier = if side == Color::White { 1 } else { -1 };
    let mut score = pesto_eval(board) * color_multiplier;

    // 2. Lazy Cutoffs
    if score - LAZY_EVAL_MARGIN >= beta {
        return score;
    }
    if score + LAZY_EVAL_MARGIN <= alpha {
        return score;
    }

    // 3. Positional Terms
    score += eval_mobility(board, tables, side) - eval_mobility(board, tables, enemy);

    // Fix: Use the standard evaluate_pawn_structure and flip for perspective
    score += evaluate_pawn_structure(board) * color_multiplier;

    // 4. Phased King Safety
    // Subtracting enemy attacks on our king, adding our attacks on theirs.
    score += calculate_phased_safety(board, side, tables)
        - calculate_phased_safety(board, enemy, tables);

    score
}

fn calculate_phased_safety(board: &Board, color: Color, tables: &MagicTables) -> i32 {
    let enemy = color.opposite();
    let phase = calculate_phase(board); // 24 = MG, 0 = EG

    let attack_count = count_king_zone_attacks(board, enemy, color, tables);
    if attack_count == 0 {
        return 0;
    }

    // Tapering logic: Penalty is 100% at phase 24 and 0% at phase 0.
    let penalty = (attack_count * KING_ZONE_ATTACK_PENALTY * phase as i32) / 24;

    -penalty // Return as negative value (a penalty)
}

fn count_king_zone_attacks(
    board: &Board,
    attacker_color: Color,
    victim_color: Color,
    tables: &MagicTables,
) -> i32 {
    let king_sq = board.king_square(victim_color);

    // Create a 3x3 bitboard zone around the king
    let b = 1u64 << king_sq.index();
    let mut king_zone = b | ((b << 1) & 0xFEFEFEFEFEFEFEFE) | ((b >> 1) & 0x7F7F7F7F7F7F7F7F);
    king_zone |= (king_zone << 8) | (king_zone >> 8);

    let mut attack_count = 0;

    // Get total occupancy bitboard
    let mut all_pieces = 0u64;
    for p in [
        Piece::Pawn,
        Piece::Knight,
        Piece::Bishop,
        Piece::Rook,
        Piece::Queen,
        Piece::King,
    ] {
        all_pieces |= board.pieces(p, Color::White) | board.pieces(p, Color::Black);
    }

    // Iterate through all attacker piece types
    for piece_type in [Piece::Knight, Piece::Bishop, Piece::Rook, Piece::Queen] {
        let mut attackers = board.pieces(piece_type, attacker_color);

        while attackers != 0 {
            let from_idx = pop_lsb(&mut attackers);
            let from_sq = Square::from_index(from_idx as u8);

            let is_attacking = match piece_type {
                // Use the new standalone function for Knight attacks
                Piece::Knight => {
                    (crate::moves::magic::get_knight_attacks(from_sq.index() as usize) & king_zone)
                        != 0
                }
                // Access inner struct for Bishop/Rook attacks
                Piece::Bishop => {
                    (tables
                        .bishop
                        .get_attacks(from_sq.index() as usize, all_pieces)
                        & king_zone)
                        != 0
                }
                Piece::Rook => {
                    (tables
                        .rook
                        .get_attacks(from_sq.index() as usize, all_pieces)
                        & king_zone)
                        != 0
                }
                Piece::Queen => {
                    ((tables
                        .bishop
                        .get_attacks(from_sq.index() as usize, all_pieces)
                        | tables
                            .rook
                            .get_attacks(from_sq.index() as usize, all_pieces))
                        & king_zone)
                        != 0
                }
                _ => false,
            };

            if is_attacking {
                attack_count += 1;
            }
        }
    }

    attack_count
}

fn eval_mobility(board: &Board, tables: &MagicTables, color: Color) -> i32 {
    let mut score = 0;
    let us_bb = board.occupancy(color);
    let them_bb = board.opponent_occupancy(color);
    let occupied = us_bb | them_bb;
    let idx = color as usize;

    // Bishops
    for sq in BitIter(board.piece_bb[idx][Piece::Bishop as usize]) {
        let attacks = tables.bishop.get_attacks(sq, occupied);
        score += (attacks & !us_bb).count_ones() as i32 * MOBILITY_WEIGHT;
    }

    // Rooks
    for sq in BitIter(board.piece_bb[idx][Piece::Rook as usize]) {
        let attacks = tables.rook.get_attacks(sq, occupied);
        score += (attacks & !us_bb).count_ones() as i32 * 3;
    }

    score
}

// --- BITWISE HELPERS ---
const FILE_A: u64 = 0x0101010101010101;
const FILE_H: u64 = 0x8080808080808080;

/// Helper: Smear pawns up and down to fill their entire file.
/// Used to detect if a file has *any* pawns efficiently.
#[inline(always)]
fn file_fill(mut pawns: u64) -> u64 {
    pawns |= pawns >> 8;
    pawns |= pawns >> 16;
    pawns |= pawns >> 32;
    pawns |= pawns << 8;
    pawns |= pawns << 16;
    pawns |= pawns << 32;
    pawns
}

pub fn evaluate_pawn_structure(board: &Board) -> i32 {
    let wp = board.pieces(Piece::Pawn, Color::White);
    let bp = board.pieces(Piece::Pawn, Color::Black);

    let mut white_score = 0;
    let mut black_score = 0;

    // --- 1. Doubled Pawns (Bitwise) ---
    // A pawn is doubled if there is another pawn of the same color behind it.
    let w_doubled_mask = wp & (wp >> 8);
    let b_doubled_mask = bp & (bp << 8);

    white_score += (w_doubled_mask.count_ones() as i32) * DOUBLED_PAWN_PENALTY;
    black_score += (b_doubled_mask.count_ones() as i32) * DOUBLED_PAWN_PENALTY;

    // --- 2. Isolated Pawns (Bitwise Parallel) ---
    // Step A: "Smear" the pawns to create a mask of files that contain at least one white pawn.
    let w_file_mask = file_fill(wp);
    let b_file_mask = file_fill(bp);

    // Step B: Calculate which files have NO neighbors.
    // Shift file mask Left and Right to find neighbor files.
    // Note: Use masks to prevent wrapping A-file to H-file.
    // Left (<< 1) moves A->B, so neighbors are to the East.
    // Right (>> 1) moves B->A, so neighbors are to the West.
    let w_neighbor_files = ((w_file_mask & !FILE_H) << 1) | ((w_file_mask & !FILE_A) >> 1);
    let b_neighbor_files = ((b_file_mask & !FILE_H) << 1) | ((b_file_mask & !FILE_A) >> 1);

    // Step C: Identify files that have pawns but NO neighbor files with pawns.
    let w_isolated_files = w_file_mask & !w_neighbor_files;
    let b_isolated_files = b_file_mask & !b_neighbor_files;

    // Step D: Intersect with actual pawns to count them.
    let w_isolated_pawns = wp & w_isolated_files;
    let b_isolated_pawns = bp & b_isolated_files;

    white_score += (w_isolated_pawns.count_ones() as i32) * ISOLATED_PAWN_PENALTY;
    black_score += (b_isolated_pawns.count_ones() as i32) * ISOLATED_PAWN_PENALTY;

    // --- 3. Passed Pawns (Simplified for now) ---
    // Keeping existing passed pawn constants but skipping logic as discussed to focus on bitwise first.
    // You can re-enable specialized passed logic later.

    white_score - black_score
}

// Renamed from evaluate to pesto_eval
pub fn pesto_eval(board: &Board) -> i32 {
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
            // FIX: Mirror White to match Table Layout (Rank 8 at index 0)
            let table_sq = mirror_vert(sq);
            mg_score += mg_val + mg_table[table_sq];
            eg_score += eg_val + eg_table[table_sq];
        }

        // Black pieces
        let mut b_bb = board.pieces(piece_type, Color::Black);
        while b_bb != 0 {
            let sq = pop_lsb(&mut b_bb);
            // FIX: Black is already at the "top", read directly
            mg_score -= mg_val + mg_table[sq as usize];
            eg_score -= eg_val + eg_table[sq as usize];
        }
    }

    // Tapered Formula
    // Score = (MG * Phase + EG * (24 - Phase)) / 24
    (mg_score * phase + eg_score * (TOTAL_PHASE - phase)) / TOTAL_PHASE
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
            let table_sq = mirror_vert(sq);
            mg_score += mg_table[table_sq];
            eg_score += eg_table[table_sq];
        }

        let mut b_bb = board.pieces(piece_type, Color::Black);
        while b_bb != 0 {
            let sq = pop_lsb(&mut b_bb);
            mg_score -= mg_table[sq as usize];
            eg_score -= eg_table[sq as usize];
        }
    }

    (mg_score * phase + eg_score * (TOTAL_PHASE - phase)) / TOTAL_PHASE
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::moves::magic::loader::load_magic_tables;
    use std::str::FromStr;

    #[test]
    fn test_lazy_eval_matches_full_eval_in_close_positions() {
        // Standard starting position
        let board = Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            .expect("Invalid FEN");
        let tables = load_magic_tables();

        // Use bounds that force full evaluation (-1000, 1000 covers the 0 score)
        let lazy = static_eval(&board, &tables, -1000, 1000);

        // Use infinite bounds to simulate "old" static eval behavior
        let full = static_eval(&board, &tables, -i32::MAX, i32::MAX);

        assert_eq!(
            lazy, full,
            "Lazy eval should equal full eval when no cutoff occurs"
        );
    }

    #[test]
    fn test_lazy_beta_cutoff() {
        // White has massive material advantage. Score ~900cp.
        let board = Board::from_str("4k3/8/8/8/8/8/QQQQQQQQ/4K3 w - - 0 1").expect("Invalid FEN");
        let tables = load_magic_tables();

        // 900 - 400 (Margin) > 100 (Beta) -> Cutoff triggers.
        let beta = 100;
        let score = static_eval(&board, &tables, -i32::MAX, beta);

        assert!(
            score > beta,
            "Should trigger cutoff and return a winning score"
        );
    }

    #[test]
    fn test_perspective_flip() {
        let board = Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            .expect("Invalid FEN");
        let tables = load_magic_tables();

        let white_eval = static_eval(&board, &tables, -i32::MAX, i32::MAX);

        let mut black_board = board.clone();
        black_board.side_to_move = Color::Black;
        let black_eval = static_eval(&black_board, &tables, -i32::MAX, i32::MAX);

        assert_eq!(white_eval, -black_eval, "Eval should be symmetric");
    }
}
