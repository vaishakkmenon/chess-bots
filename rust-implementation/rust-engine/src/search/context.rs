use crate::moves::types::Move;

const MAX_PLY: usize = 64;

pub struct SearchContext {
    /// Store 2 killer moves per ply level
    /// killers[ply][0] = primary killer (most recent)
    /// killers[ply][1] = secondary killer
    pub killers: [[Option<Move>; 2]; MAX_PLY],
}

impl SearchContext {
    pub fn new() -> Self {
        Self {
            killers: [[None; 2]; MAX_PLY],
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

    /// Check if a move is a killer at this ply
    pub fn is_killer(&self, ply: usize, mv: &Move) -> bool {
        if ply >= MAX_PLY {
            return false;
        }

        self.killers[ply][0] == Some(*mv) || self.killers[ply][1] == Some(*mv)
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
        assert!(ctx.is_killer(0, &mv1));

        ctx.update_killer(0, mv2);
        assert!(ctx.is_killer(0, &mv1));
        assert!(ctx.is_killer(0, &mv2));

        assert!(!ctx.is_killer(1, &mv1));
    }
}
