use crate::board::Piece;
use crate::moves::types::Move;
use crate::square::Square;

const MAX_PLY: usize = 64;

pub struct SearchContext {
    /// Store 2 killer moves per ply level
    /// killers[ply][0] = primary killer (most recent)
    /// killers[ply][1] = secondary killer
    pub killers: [[Option<Move>; 2]; MAX_PLY],
    pub history: [[i32; 64]; 6],
    pub tt_move: Option<Move>,

    #[cfg(feature = "lmr_stats")]
    pub lmr_reductions: u64,
    #[cfg(feature = "lmr_stats")]
    pub lmr_researches: u64,
}

impl SearchContext {
    pub fn new() -> Self {
        Self {
            killers: [[None; 2]; MAX_PLY],
            history: [[0; 64]; 6],
            tt_move: None,
            #[cfg(feature = "lmr_stats")]
            lmr_reductions: 0,
            #[cfg(feature = "lmr_stats")]
            lmr_researches: 0,
        }
    }

    /// Update killer moves when a quiet move causes beta cutoff
    pub fn update_killer(&mut self, ply: usize, mv: Move) {
        // Bounds check
        if ply >= MAX_PLY {
            return;
        }

        // Don't store if it's already the primary killer
        if self.killers[ply][0] == Some(mv) {
            return;
        }

        // Shift: primary -> secondary, new move -> primary
        self.killers[ply][1] = self.killers[ply][0];
        self.killers[ply][0] = Some(mv);
    }

    /// Update history when a quiet move causes beta cutoff
    pub fn update_history(&mut self, piece: Piece, to: Square, depth: i32) {
        let piece_idx = piece as usize;
        let square_idx = to.index() as usize;
        let bonus = depth.saturating_mul(depth);

        // Depth-squared bonus: deeper searches are more important
        self.history[piece_idx][square_idx] =
            self.history[piece_idx][square_idx].saturating_add(bonus);
    }

    /// Get history score for a move
    pub fn history_score(&self, piece: Piece, to: Square) -> i32 {
        let piece_idx = piece as usize;
        let square_idx = to.index() as usize;
        self.history[piece_idx][square_idx]
    }

    /// Check if a move is a killer at this ply
    pub fn is_killer(&self, ply: usize, mv: Move) -> bool {
        if ply >= MAX_PLY {
            return false;
        }

        self.killers[ply][0] == Some(mv) || self.killers[ply][1] == Some(mv)
    }

    /// Clear history at start of new search
    pub fn clear_history(&mut self) {
        self.history = [[0; 64]; 6];
    }

    pub fn set_best_move(&mut self, mv: Move) {
        self.tt_move = Some(mv);
    }

    pub fn get_best_move(&self) -> Option<Move> {
        self.tt_move
    }

    #[cfg(feature = "lmr_stats")]
    #[inline]
    pub fn reset_lmr_stats(&mut self) {
        self.lmr_reductions = 0;
        self.lmr_researches = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::Piece;
    use crate::moves::types::Move;
    use crate::square::Square;
    use std::str::FromStr;

    #[test]
    fn test_killer_storage() {
        let mut ctx = SearchContext::new();

        let mv1 = Move {
            piece: Piece::Pawn,
            from: Square::from_str("e2").unwrap(),
            to: Square::from_str("e4").unwrap(),
            promotion: None,
            flags: 0,
        };

        let mv2 = Move {
            piece: Piece::Knight,
            from: Square::from_str("g1").unwrap(),
            to: Square::from_str("f3").unwrap(),
            promotion: None,
            flags: 0,
        };

        ctx.update_killer(0, mv1);
        assert!(ctx.is_killer(0, mv1));

        ctx.update_killer(0, mv2);
        assert!(ctx.is_killer(0, mv1));
        assert!(ctx.is_killer(0, mv2));

        assert!(!ctx.is_killer(1, mv1));
    }
}
