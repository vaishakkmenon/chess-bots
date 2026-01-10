use crate::moves::types::Move;

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum NodeType {
    Exact,      // PV node
    LowerBound, // Failed high (beta cutoff)
    UpperBound, // Failed low (all moves < alpha)
}

#[derive(Clone, Copy)]
pub struct TTEntry {
    pub hash: u64,
    pub depth: i8,
    pub score: i32,
    pub best_move: Option<Move>,
    pub node_type: NodeType,
}

pub struct TranspositionTable {
    table: Vec<Option<TTEntry>>,
    size: usize,
}

impl TranspositionTable {
    pub fn new(size: usize) -> Self {
        Self {
            table: vec![None; size],
            size,
        }
    }

    pub fn size(&self) -> usize {
        self.size
    }

    fn index(&self, hash: u64) -> usize {
        (hash as usize) % self.size
    }

    pub fn probe(&self, hash: u64) -> Option<&TTEntry> {
        let index = self.index(hash);
        if let Some(entry) = &self.table[index] {
            if entry.hash == hash {
                return Some(entry);
            }
        }
        None
    }

    pub fn store(
        &mut self,
        hash: u64,
        depth: i8,
        score: i32,
        best_move: Option<Move>,
        node_type: NodeType,
    ) {
        let index = self.index(hash);

        // Check what is currently in the slot
        if let Some(existing) = &self.table[index] {
            // Rule 1: Always replace if we are searching deeper than the stored entry
            if depth > existing.depth {
                self.table[index] = Some(TTEntry {
                    hash,
                    score,
                    best_move,
                    depth,
                    node_type,
                });
                return;
            }

            // Rule 2: If depths are equal, be careful!
            if depth == existing.depth {
                // NEVER overwrite an EXACT node with a BOUND node at the same depth
                if existing.node_type == NodeType::Exact && node_type != NodeType::Exact {
                    return;
                }

                // Otherwise (Exact overwrites Exact, or Bound overwrites Bound), update it.
                // We also generally want to keep the 'best_move' if the new entry doesn't have one.
                let new_best_move = best_move.or(existing.best_move);

                self.table[index] = Some(TTEntry {
                    hash,
                    score,
                    best_move: new_best_move,
                    depth,
                    node_type,
                });
                return;
            }

            // Rule 3: If new depth is shallower (depth < existing.depth), do nothing.
            // We want to keep the deeper search result.
        } else {
            // Slot is empty, just store it
            self.table[index] = Some(TTEntry {
                hash,
                score,
                best_move,
                depth,
                node_type,
            });
        }
    }
}
