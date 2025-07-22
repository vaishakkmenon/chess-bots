use super::attacks::*;
use super::masks::*;
use super::search::*;
use super::structs::*;
use crate::utils::enumerate_subsets;

pub fn precompute_rook_attacks() -> Vec<Vec<u64>> {
    let mut table = Vec::with_capacity(64);

    for square in 0..64 {
        let mask = rook_vision_mask(square);

        let mut subsets = Vec::new();
        enumerate_subsets(mask, |subset| {
            subsets.push(subset);
        });

        let mut attacks_for_square = Vec::with_capacity(subsets.len());

        for blockers in subsets {
            let attacks = rook_attacks_per_square(square, blockers);
            attacks_for_square.push(attacks);
        }

        table.push(attacks_for_square);
    }

    return table;
}

pub fn precompute_bishop_attacks() -> Vec<Vec<u64>> {
    let mut table = Vec::with_capacity(64);

    for square in 0..64 {
        let mask = bishop_vision_mask(square);

        let mut subsets = Vec::new();
        enumerate_subsets(mask, |subset| {
            subsets.push(subset);
        });

        let mut attacks_for_square = Vec::with_capacity(subsets.len());

        for blockers in subsets {
            let attacks = bishop_attacks_per_square(square, blockers);
            attacks_for_square.push(attacks);
        }

        table.push(attacks_for_square);
    }

    return table;
}

/// Generates a full set of 64 `MagicEntry`s for a sliding piece (e.g. rook or bishop)
/// by building magic bitboard lookup tables for each square.
///
/// # Parameters
/// - `piece_name`: A string label used only for logging.
/// - `gen_blockers`: Function that returns all possible blocker permutations for a given square.
/// - `get_attacks`: Function that returns the expected attack bitboards for all blocker permutations.
/// - `get_mask`: Function that returns the vision mask for a given square.
/// - `attacks_per_square`: Function that returns the actual attack bitboard for a given square and blocker configuration.
///
/// # Returns
/// An array of 64 `MagicEntry`s, one for each square on the board. Each entry contains:
/// - a magic number (used for hashing blocker configurations),
/// - a shift value (how many bits to shift the hash down),
/// - and a lookup table mapping hashed blockers to precomputed attacks.
///
/// # How It Works
/// For each square:
/// 1. All blocker permutations within the piece's vision mask are generated.
/// 2. The corresponding attack bitboards are computed.
/// 3. A "magic" number is found that produces a unique index for each blocker configuration.
/// 4. A lookup table is populated using these magic indices.
///
/// # Panics
/// Panics if the final `Vec<MagicEntry>` does not contain exactly 64 entries. This
/// would indicate a logic error in how blockers were generated or processed.

fn generate_magic_entries<FBlockers, FAttacks, FMask, FPerSquare>(
    piece_name: &str,
    gen_blockers: FBlockers,
    get_attacks: FAttacks,
    get_mask: FMask,
    attacks_per_square: FPerSquare,
) -> [MagicEntry; 64]
where
    FBlockers: Fn(usize) -> Vec<u64>,
    FAttacks: Fn(usize, &[u64]) -> Vec<u64>,
    FMask: Fn(usize) -> u64,
    FPerSquare: Fn(usize, u64) -> u64,
{
    let mut entries_vec = Vec::with_capacity(64);

    for square in 0..64 {
        println!("Generating {} magic for square {}", piece_name, square);

        let blockers = gen_blockers(square);
        let attacks = get_attacks(square, &blockers);
        let mask = get_mask(square);
        let shift = 64 - mask.count_ones();
        let magic = find_magic_number_for_square(&blockers, &attacks, shift);

        let table_size = 1 << mask.count_ones();
        let mut table = vec![0u64; table_size];

        for &b in &blockers {
            let idx = ((b & mask).wrapping_mul(magic)) >> shift;
            table[idx as usize] = attacks_per_square(square, b);
        }

        entries_vec.push(MagicEntry {
            magic,
            shift,
            table,
        });
    }

    entries_vec
        .try_into()
        .expect("Expected 64 entries for magic generation")
}

pub fn generate_rook_magic_tables() -> RookMagicTables {
    RookMagicTables {
        entries: generate_magic_entries(
            "rook",
            generate_rook_blockers,
            get_rook_attack_bitboards,
            rook_vision_mask,
            rook_attacks_per_square,
        ),
    }
}

pub fn generate_bishop_magic_tables() -> BishopMagicTables {
    BishopMagicTables {
        entries: generate_magic_entries(
            "bishop",
            generate_bishop_blockers,
            get_bishop_attack_bitboards,
            bishop_vision_mask,
            bishop_attacks_per_square,
        ),
    }
}
