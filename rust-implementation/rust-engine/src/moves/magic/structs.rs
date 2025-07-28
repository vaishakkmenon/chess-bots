use serde::{Deserialize, Serialize};

/// A single magic bitboard entry used to compute sliding piece attacks.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MagicEntry {
    /// The magic number used to hash blocker bitboards into attack indices.
    pub magic: u64,

    /// The number of bits to shift after multiplication to get the table index.
    pub shift: u32,

    /// The precomputed attack table indexed by (blockers * magic) >> shift.
    pub table: Box<[u64]>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RookMagicTables {
    pub entries: Vec<MagicEntry>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BishopMagicTables {
    pub entries: Vec<MagicEntry>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MagicTables {
    pub rook: RookMagicTables,
    pub bishop: BishopMagicTables,
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

impl MagicTables {
    /// Returns queen attacks by combining rook and bishop magic lookups.
    pub fn queen_attacks(&self, square: usize, blockers: u64) -> u64 {
        let rook_mask = crate::moves::magic::masks::rook_vision_mask(square);
        let bishop_mask = crate::moves::magic::masks::bishop_vision_mask(square);

        let rook = self.rook.get_attacks(square, blockers, rook_mask);
        let bishop = self.bishop.get_attacks(square, blockers, bishop_mask);

        rook | bishop
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::moves::magic::attacks::{bishop_attacks_per_square, rook_attacks_per_square};
    use crate::moves::magic::masks::{bishop_vision_mask, rook_vision_mask};
    use crate::moves::magic::precompute::{MagicTableSeed, generate_magic_tables};

    /// One constant seed for repeatable results (0x45 == 69 decimal)
    const TEST_SEED: u64 = 0x45;

    /// Build **both** magic tables once per test
    fn build_tables() -> MagicTables {
        generate_magic_tables(MagicTableSeed::Fixed(TEST_SEED))
            .expect("Failed to generate magic tables")
    }

    // ──────────────────────────────────────────────────────────────────────────
    //  1.  Debug print still compiles
    // ──────────────────────────────────────────────────────────────────────────
    #[test]
    fn test_debug_print_rook() {
        let tables = build_tables();
        println!("{:?}", tables.rook); // just needs to compile / run
    }

    // ──────────────────────────────────────────────────────────────────────────
    //  2.  Bishop magic lookup matches scan generator
    // ──────────────────────────────────────────────────────────────────────────
    #[test]
    fn test_bishop_magic_lookup_matches_scan() {
        // square d4  (3 + 3*8) == 27
        let square = 27;
        let blockers = (1u64 << 41) | (1u64 << 21); // B6 + F2
        let mask = bishop_vision_mask(square);

        let expected = bishop_attacks_per_square(square, blockers);

        let tables = build_tables();
        let result = tables.bishop.get_attacks(square, blockers, mask);

        assert_eq!(
            result, expected,
            "Magic lookup result does not match scan-based bishop attack generation"
        );
    }

    // ──────────────────────────────────────────────────────────────────────────
    //  3.  Rook magic lookup matches scan generator
    // ──────────────────────────────────────────────────────────────────────────
    #[test]
    fn test_rook_magic_lookup_matches_scan() {
        let square = 27; // d4
        let blockers = (1u64 << 19) | (1u64 << 35); // d3 + d6
        let mask = rook_vision_mask(square);

        let expected = rook_attacks_per_square(square, blockers);

        let tables = build_tables();
        let result = tables.rook.get_attacks(square, blockers, mask);

        assert_eq!(
            result, expected,
            "Magic lookup result does not match scan-based rook attack generation"
        );
    }

    // ──────────────────────────────────────────────────────────────────────────
    //  4.  Queen attacks == rook ∪ bishop
    // ──────────────────────────────────────────────────────────────────────────
    #[test]
    fn test_queen_magic_lookup_matches_combined() {
        let square = 27; // d4
        let blockers = (1u64 << 19) | (1u64 << 35) | (1u64 << 41) | (1u64 << 21);

        let rook_expected = rook_attacks_per_square(square, blockers);
        let bishop_expected = bishop_attacks_per_square(square, blockers);
        let expected = rook_expected | bishop_expected;

        let tables = build_tables();
        let result = tables.queen_attacks(square, blockers);

        assert_eq!(
            result, expected,
            "Queen magic lookup does not match combined scan logic"
        );
    }
}
