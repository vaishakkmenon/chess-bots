/// A single magic bitboard entry used to compute sliding piece attacks.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MagicEntry {
    /// The magic number used to hash blocker bitboards into attack indices.
    pub magic: u64,

    /// The number of bits to shift after multiplication to get the table index.
    pub shift: u32,

    /// The precomputed attack table indexed by (blockers * magic) >> shift.
    pub table: Box<[u64]>,
}

#[derive(Debug)]
pub struct RookMagicTables {
    pub entries: [MagicEntry; 64],
}

#[derive(Debug)]
pub struct BishopMagicTables {
    pub entries: [MagicEntry; 64],
}

#[cfg(test)]
#[test]
fn test_debug_print_rook() {
    use std::array;

    let dummy_entry = MagicEntry {
        magic: 0x1234_5678_9ABC_DEF0,
        shift: 52,
        table: vec![0; 4096].into_boxed_slice(),
    };

    let rook_tables = RookMagicTables {
        entries: array::from_fn(|_| dummy_entry.clone()),
    };

    println!("{:?}", rook_tables); // Should compile and print without issues
}
