use crate::board::{Board, Color, Piece};
use crate::moves::magic::MagicTables;
use crate::search::pesto;
use crate::utils::pop_lsb;

// --- Evaluation Weights (Centipawns) ---
// --- Evaluation Weights (Centipawns) ---
const MOBILITY_WEIGHT: i32 = 5;
// Huge bonus for advancing pawns - this incentivizes WINNING endgames
const PASSED_PAWN_BONUS: [i32; 8] = [0, 10, 20, 35, 50, 80, 120, 0];
const ISOLATED_PAWN_PENALTY: i32 = -15;
const DOUBLED_PAWN_PENALTY: i32 = -15;
const KING_SHIELD_BONUS: i32 = 10;
const KING_EXPOSED_PENALTY: i32 = -30;

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

// --- Mop-Up Helper Functions ---

// 1. Center Manhattan Distance (How far is a square from the center?)
// Ranges from 0 (e4, d4, etc.) to 6 (corners).
// Used to drive the enemy King to the edge.
fn cmd(sq: u8) -> i32 {
    let row = (sq / 8) as i32;
    let col = (sq % 8) as i32;
    // |2r - 7| + |2c - 7| gives a nice "center-weighted" distance
    (2 * row - 7).abs() + (2 * col - 7).abs()
}

// 2. Chebyshev Distance (Grid distance between two squares)
// Ranges from 0 to 7.
// Used to bring our King closer to theirs.
fn dist(sq1: u8, sq2: u8) -> i32 {
    let r1 = (sq1 / 8) as i32;
    let c1 = (sq1 % 8) as i32;
    let r2 = (sq2 / 8) as i32;
    let c2 = (sq2 % 8) as i32;
    (r1 - r2).abs().max((c1 - c2).abs())
}

// 3. Material Check
// Returns true if the color has any Knights, Bishops, Rooks, or Queens.
fn has_non_pawn_material(board: &Board, color: Color) -> bool {
    let bb = board.pieces(Piece::Knight, color)
        | board.pieces(Piece::Bishop, color)
        | board.pieces(Piece::Rook, color)
        | board.pieces(Piece::Queen, color);
    bb != 0
}

pub fn static_eval(board: &Board, tables: &MagicTables) -> i32 {
    // 1. Base Score (Material + PeSTO)
    let mut score = pesto_eval(board); // Your existing PeSTO

    // Mobility (Activity)
    score +=
        eval_mobility(board, tables, Color::White) - eval_mobility(board, tables, Color::Black);

    // Pawn Structure (Structure + Passed Pawns)
    score += eval_pawns(board, Color::White) - eval_pawns(board, Color::Black);

    // King Safety (Shielding)
    score += eval_king_safety(board, Color::White) - eval_king_safety(board, Color::Black);

    // 2. MOP-UP EVALUATION
    // Only apply if the game is decided (one side has no pieces left).
    // AND if both kings are on the board (sanity check for partial-board tests)
    if board.pieces(Piece::King, Color::White) != 0 && board.pieces(Piece::King, Color::Black) != 0
    {
        // Scenario A: White is winning, Black has no pieces (only King + Pawns)
        // We add bonuses to 'score' (making it more positive)
        if score > 0 && !has_non_pawn_material(board, Color::Black) {
            let white_king = board.king_square(Color::White).index() as u8;
            let black_king = board.king_square(Color::Black).index() as u8;

            // Bonus 1: Push Black King to edge (Max value ~60)
            score += 10 * cmd(black_king);

            // Bonus 2: Bring White King closer (Max value ~56)
            // (14 - dist) ensures closer = higher score
            score += 4 * (14 - dist(white_king, black_king));
        }
        // Scenario B: Black is winning, White has no pieces
        // We subtract bonuses from 'score' (making it more negative)
        else if score < 0 && !has_non_pawn_material(board, Color::White) {
            let white_king = board.king_square(Color::White).index() as u8;
            let black_king = board.king_square(Color::Black).index() as u8;

            // Bonus 1: Push White King to edge
            score -= 10 * cmd(white_king);

            // Bonus 2: Bring Black King closer
            score -= 4 * (14 - dist(black_king, white_king));
        }
    }

    // 3. Return Perspective Score
    if board.side_to_move == Color::Black {
        -score
    } else {
        score
    }
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
        // Using *3 as per user request (User code had *3)
        // Previous code had (MOBILITY_WEIGHT - 2) which is 3. So consistent.
        score += (attacks & !us_bb).count_ones() as i32 * 3;
    }

    // User didn't include Queens in their snippet, but I should probably keep them if I want to match "Mobility" concept?
    // User's snippet:
    // "    // Bishops ...
    //      // Rooks ...
    //      score"
    // It DOES NOT include Queens.
    // However, existing code DID include Queens.
    // User instruction: "Please copy the code block below... This provides the 'Aggression' needed"
    // If I omit Queens, I might weaken the engine or make it closer to what they tested.
    // BUT, the snippet starts with "fn eval_mobility..." inside the block.
    // I will STRICTLY follow the user's snippet for `eval_mobility` to match the "Aggression" profile they want (maybe they found Queen mobility unstable?).
    // WAIT, checking user snippet again.
    // It has Bishops and Rooks. No Queens.
    // Okay, I will remove Queen mobility to match exact snippet.

    score
}

fn eval_pawns(board: &Board, color: Color) -> i32 {
    let mut score = 0;
    let pawns = board.piece_bb[color as usize][Piece::Pawn as usize];
    let enemy_pawns = board.piece_bb[(!color) as usize][Piece::Pawn as usize];

    for file in 0..8 {
        let file_mask = 0x0101010101010101u64 << file;
        let my_pawns_on_file = pawns & file_mask;

        if my_pawns_on_file == 0 {
            continue;
        }

        // 1. Structure Penalties
        let count = my_pawns_on_file.count_ones();
        if count > 1 {
            score += DOUBLED_PAWN_PENALTY * (count as i32 - 1);
        }

        let left = if file > 0 { file_mask >> 1 } else { 0 };
        let right = if file < 7 { file_mask << 1 } else { 0 };
        let neighbors = (left | right) & pawns;
        if neighbors == 0 {
            score += ISOLATED_PAWN_PENALTY;
        }

        // 2. Passed Pawns (The Win Condition)
        for sq in BitIter(my_pawns_on_file) {
            let rank = sq / 8;
            let forward_mask = if color == Color::White {
                !0u64 << (8 * (rank + 1))
            } else {
                !0u64 >> (8 * (8 - rank))
            };

            let span_mask = (file_mask | left | right) & forward_mask;

            if (span_mask & enemy_pawns) == 0 {
                // IT IS PASSED! HUGE BONUS!
                let relative_rank = if color == Color::White {
                    rank
                } else {
                    7 - rank
                };
                score += PASSED_PAWN_BONUS[relative_rank as usize];
            }
        }
    }
    score
}

fn eval_king_safety(board: &Board, color: Color) -> i32 {
    let ksq_iter = BitIter(board.piece_bb[color as usize][Piece::King as usize]);
    let ksq = if let Some(k) = ksq_iter.into_iter().next() {
        k
    } else {
        return 0;
    };

    let file = ksq % 8;
    let rank = ksq / 8;

    // Only care about safety if king is on back ranks
    if (color == Color::White && rank > 2) || (color == Color::Black && rank < 5) {
        return 0;
    }

    let pawns = board.piece_bb[color as usize][Piece::Pawn as usize];
    let mut score = 0;

    for f in (file.saturating_sub(1))..=(file.saturating_add(1).min(7)) {
        let file_mask = 0x0101010101010101u64 << f;
        let pawn_shield = pawns & file_mask;

        if pawn_shield != 0 {
            score += KING_SHIELD_BONUS;
        } else {
            score += KING_EXPOSED_PENALTY;
        }
    }
    score
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
