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

impl RookMagicTables {
    /// Returns the rook attack bitboard for a given square, blockers, and vision mask.
    /// The mask should be the rook vision mask for that square.
    pub fn get_attacks(&self, square: usize, blockers: u64, mask: u64) -> u64 {
        let entry = &self.entries[square];
        let masked = blockers & mask;
        let index = ((masked.wrapping_mul(entry.magic)) >> entry.shift) as usize;
        entry.table[index]
    }
}

impl BishopMagicTables {
    /// Returns the bishop attack bitboard for a given square, blockers, and vision mask.
    /// The mask should be the bishop vision mask for that square.
    pub fn get_attacks(&self, square: usize, blockers: u64, mask: u64) -> u64 {
        let entry = &self.entries[square];
        let masked = blockers & mask;
        let index = ((masked.wrapping_mul(entry.magic)) >> entry.shift) as usize;
        entry.table[index]
    }
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

#[test]
fn test_bishop_magic_lookup_matches_scan() {
    use crate::moves::magic::attacks::bishop_attacks_per_square;
    use crate::moves::magic::masks::bishop_vision_mask;
    use crate::moves::magic::precompute::generate_bishop_magic_tables;

    // Pick a test square: D4 (index 27)
    let square = 27;

    // Place hypothetical blockers along diagonals
    let blockers = (1u64 << 41) | // B6
    (1u64 << 21); // F2

    // Get vision mask for the square (used in indexing)
    let mask = bishop_vision_mask(square);

    // Ground truth using scan-based attack generator
    let expected = bishop_attacks_per_square(square, blockers);

    // Load the actual bishop magic tables
    let table = generate_bishop_magic_tables().expect("Failed to generate bishop magic table");

    // Do magic lookup
    let result = table.get_attacks(square, blockers, mask);

    assert_eq!(
        result, expected,
        "Magic lookup result does not match scan-based bishop attack generation"
    );
}

#[test]
fn test_rook_magic_lookup_matches_scan() {
    use crate::moves::magic::attacks::rook_attacks_per_square;
    use crate::moves::magic::masks::rook_vision_mask;
    use crate::moves::magic::precompute::generate_rook_magic_tables;

    let square = 27; // D4
    let blockers = (1u64 << 19) | (1u64 << 35); // D3 and D6
    let mask = rook_vision_mask(square);

    let expected = rook_attacks_per_square(square, blockers);

    let table = generate_rook_magic_tables().expect("Failed to generate rook magic table");

    let result = table.get_attacks(square, blockers, mask);

    assert_eq!(
        result, expected,
        "Magic lookup result does not match scan-based rook attack generation"
    );
}
