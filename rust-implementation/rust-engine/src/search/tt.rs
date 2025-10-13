use crate::moves::types::Move;
use crate::search::search::is_mate_score;

pub struct TranspositionTable {
    entries: Vec<TTEntry>,
    size: usize, // Always power of 2
    age: u8,     // Incremented each search
}

#[derive(Clone)]
pub struct TTEntry {
    zobrist_key: u64,        // 8 bytes
    best_move: Option<Move>, // 8 bytes (if Move is 64-bit)
    score: i16,              // 2 bytes (centipawns fit in i16)
    depth: i8,               // 1 byte
    node_type: NodeType,     // 1 byte (0=None, 1=Exact, 2=Lower, 3=Upper)
    age: u8,                 // 1 byte
}

#[derive(Clone, Copy, PartialEq)]
pub enum NodeType {
    Empty,
    Exact,      // We searched all moves, this is the exact score
    LowerBound, // Beta cutoff happened, real score >= this
    UpperBound, // All moves failed low, real score <= this
}

pub struct ProbeResult {
    pub score: Option<i32>,
    pub best_move: Option<Move>,
}

impl TranspositionTable {
    pub fn new(size_mb: usize) -> Self {
        // Calculate number of entries
        // Each entry is ~32 bytes, so 1 MB = ~32,000 entries
        let entry_size = std::mem::size_of::<TTEntry>();
        let num_entries = (size_mb * 1024 * 1024) / entry_size;

        // Round down to nearest power of 2 for fast modulo
        let num_entries = num_entries.next_power_of_two() / 2;

        TranspositionTable {
            entries: vec![TTEntry::default(); num_entries],
            size: num_entries,
            age: 0,
        }
    }

    pub fn probe(
        &self,
        zobrist_hash: u64,
        depth: i32,
        alpha: i32,
        beta: i32,
        ply: i32,
    ) -> ProbeResult {
        let mut result = ProbeResult::default();
        let index = (zobrist_hash as usize) & (self.size - 1);
        let entry = &self.entries[index];

        // Collision check
        if entry.zobrist_key != zobrist_hash {
            return result;
        }

        // ALWAYS return the TT move if we have it (even if depth insufficient)
        result.best_move = entry.best_move;

        // Only return score if depth is sufficient
        if entry.depth < depth as i8 {
            return result;
        }

        let mut score = entry.score as i32;

        // Adjust mate scores back to root perspective
        if is_mate_score(score) {
            score = if score > 0 {
                score + ply // We can mate: add ply back
            } else {
                score - ply // We get mated: subtract ply
            };
        }

        // Determine if we can return a score cutoff
        match entry.node_type {
            NodeType::Exact => {
                result.score = Some(score);
            }
            NodeType::LowerBound => {
                if score >= beta {
                    result.score = Some(beta);
                }
            }
            NodeType::UpperBound => {
                if score <= alpha {
                    result.score = Some(alpha);
                }
            }
            NodeType::Empty => {}
        }

        result
    }

    fn should_replace(&self, old: &TTEntry, new_depth: i8) -> bool {
        old.node_type == NodeType::Empty || old.age != self.age || new_depth >= old.depth
    }

    pub fn store(
        &mut self,
        zobrist_hash: u64,
        depth: i32,
        mut score: i32,
        best_move: Option<Move>,
        node_type: NodeType,
        ply: i32,
    ) {
        if is_mate_score(score) {
            score = if score > 0 {
                score - ply // We can mate opponent: subtract ply
            } else {
                score + ply // We get mated: add ply
            };
        }

        // 1. Get index from hash
        let index = (zobrist_hash as usize) & (self.size - 1);
        // 2. Decide if we should replace the existing entry
        if self.should_replace(&self.entries[index], depth as i8) {
            // 3. Create new entry and store it
            self.entries[index] = TTEntry {
                zobrist_key: zobrist_hash,
                best_move,
                score: score as i16,
                depth: depth as i8,
                node_type,
                age: self.age,
            };
        }
    }
}

impl Default for TTEntry {
    fn default() -> Self {
        TTEntry {
            zobrist_key: 0,
            best_move: None,
            score: 0,
            depth: 0,
            node_type: NodeType::Empty,
            age: 0,
        }
    }
}

impl Default for ProbeResult {
    fn default() -> Self {
        ProbeResult {
            score: None,
            best_move: None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_table() {
        let tt = TranspositionTable::new(64); // 64 MB
        println!("Created table with {} entries", tt.size);
        assert!(tt.size > 0);
        assert!(tt.size.is_power_of_two());
    }

    #[test]
    fn test_probe_miss() {
        let tt = TranspositionTable::new(1);
        let result = tt.probe(12345, 5, -1000, 1000, 0);

        // ProbeResult is always returned, check if it's empty
        assert!(
            result.score.is_none(),
            "Should not get score on empty table"
        );
        assert!(
            result.best_move.is_none(),
            "Should not get move on empty table"
        );
    }

    #[test]
    fn test_store_and_retrieve() {
        let mut tt = TranspositionTable::new(1);

        // Store a position
        tt.store(12345, 5, 100, None, NodeType::Exact, 0);

        // Retrieve it
        let result = tt.probe(12345, 5, -1000, 1000, 0);

        // Check we got a score
        assert!(result.score.is_some(), "Should get score from TT");
        assert_eq!(result.score.unwrap(), 100);
    }

    #[test]
    fn test_depth_replacement() {
        let mut tt = TranspositionTable::new(1);

        // Store shallow search
        tt.store(12345, 3, 100, None, NodeType::Exact, 0);

        // Store deeper search (should replace)
        tt.store(12345, 5, 200, None, NodeType::Exact, 0);

        // Should get the deeper search result
        let result = tt.probe(12345, 5, -1000, 1000, 0);
        assert!(result.score.is_some());
        assert_eq!(result.score.unwrap(), 200);
    }

    #[test]
    fn test_probe_returns_move_even_without_score() {
        let mut tt = TranspositionTable::new(1);

        // Create a dummy move for testing
        use crate::board::Piece;
        use crate::moves::types::Move;
        use crate::square::Square;
        let test_move = Move {
            from: Square::from_index(1), // b1
            to: Square::from_index(18),  // c3 (up 2, right 1 - valid L-shape)
            piece: Piece::Knight,
            promotion: None,
            flags: 0,
        };

        // Store a move at depth 3
        tt.store(12345, 3, 100, Some(test_move), NodeType::Exact, 0);

        // Probe at depth 5 (depth insufficient for score cutoff)
        let result = tt.probe(12345, 5, -1000, 1000, 0);

        // Should NOT get score (depth insufficient)
        assert!(
            result.score.is_none(),
            "Should not get score when depth insufficient"
        );

        // But SHOULD get the TT move!
        assert!(
            result.best_move.is_some(),
            "Should still get TT move for ordering"
        );
        assert_eq!(result.best_move.unwrap(), test_move);
    }

    #[test]
    fn test_probe_returns_move_even_without_cutoff() {
        let mut tt = TranspositionTable::new(1);

        // Create a test move
        use crate::board::Piece;
        use crate::moves::types::Move;
        use crate::square::Square;
        let test_move = Move {
            from: Square::from_index(1), // b1
            to: Square::from_index(18),  // c3 (up 2, right 1 - valid L-shape)
            piece: Piece::Knight,
            promotion: None,
            flags: 0,
        };

        // Store a move at depth 5
        tt.store(12345, 5, 100, Some(test_move), NodeType::Exact, 0);

        // Probe at depth 10 (insufficient depth for score cutoff)
        let result = tt.probe(12345, 10, -1000, 1000, 0);

        // Should NOT get score (depth insufficient)
        assert!(
            result.score.is_none(),
            "Should not get score when depth insufficient"
        );

        // But SHOULD get the TT move!
        assert!(
            result.best_move.is_some(),
            "Should still get TT move for move ordering"
        );
        assert_eq!(
            result.best_move.unwrap(),
            test_move,
            "TT move should match stored move"
        );
    }

    #[test]
    fn test_mate_score_adjustment() {
        use crate::search::search::MATE;
        let mut tt = TranspositionTable::new(1);

        // Store mate-in-3 at ply 4
        let mate_in_3 = MATE - 3;
        tt.store(12345, 5, mate_in_3, None, NodeType::Exact, 4); // ← ply = 4

        // Probe at ply 2 (closer to root)
        let result = tt.probe(12345, 5, -100000, 100000, 2); // ← ply = 2

        // Should be adjusted to mate-in-5 from root
        // Stored: (MATE - 3) - 4 = MATE - 7
        // Retrieved: (MATE - 7) + 2 = MATE - 5
        assert_eq!(result.score.unwrap(), MATE - 5);
    }

    #[test]
    fn test_mated_score_adjustment() {
        use crate::search::search::MATE;
        let mut tt = TranspositionTable::new(1);

        // Store getting-mated-in-2 at ply 3
        let mated_in_2 = -(MATE - 2);
        tt.store(54321, 5, mated_in_2, None, NodeType::Exact, 3); // ← ply = 3

        // Probe at ply 1 (closer to root)
        let result = tt.probe(54321, 5, -100000, 100000, 1); // ← ply = 1

        // Should be adjusted to mated-in-4 from root
        // Stored: -(MATE - 2) + 3 = -(MATE - 5)
        // Retrieved: -(MATE - 5) - 1 = -(MATE - 4)
        assert_eq!(result.score.unwrap(), -(MATE - 4));
    }
}
