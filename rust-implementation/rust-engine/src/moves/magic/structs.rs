#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MagicEntry {
    pub magic: u64,
    pub shift: u32,
    pub table: Vec<u64>,
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
        table: vec![0; 4096],
    };

    let rook_tables = RookMagicTables {
        entries: array::from_fn(|_| dummy_entry.clone()),
    };

    println!("{:?}", rook_tables); // Should compile and print without issues
}
