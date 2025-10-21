use crate::moves::types::Move;

#[derive(Clone, Copy)]
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
        if self.table[index].is_none() || self.table[index].unwrap().depth <= depth {
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
