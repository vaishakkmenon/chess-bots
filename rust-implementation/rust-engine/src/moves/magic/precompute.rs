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

pub fn generate_rook_magic_tables() -> RookMagicTables {
    let mut entries_vec = Vec::with_capacity(64);

    for square in 0..64 {
        println!("Generating rook magic for square {}", square);

        let blockers = generate_rook_blockers(square);
        let attacks = get_rook_attack_bitboards(square, &blockers);

        let mask = rook_vision_mask(square);
        let shift = 64 - mask.count_ones();
        let magic = find_magic_number_for_square(&blockers, &attacks, shift);

        let table_size = 1 << mask.count_ones();
        let mut table = vec![0u64; table_size];

        for &b in &blockers {
            let idx = ((b & mask).wrapping_mul(magic)) >> shift;
            table[idx as usize] = rook_attacks_per_square(square, b);
        }

        entries_vec.push(MagicEntry {
            magic,
            shift,
            table,
        });
    }

    let entries: [MagicEntry; 64] = entries_vec
        .try_into()
        .expect("Expected exactly 64 entries for magic table generation");

    return RookMagicTables { entries };
}

pub fn generate_bishop_magic_tables() -> BishopMagicTables {
    let mut entries_vec = Vec::with_capacity(64);

    for square in 0..64 {
        println!("Generating bishop magic for square {}", square);

        let blockers = generate_bishop_blockers(square);
        let attacks = get_bishop_attack_bitboards(square, &blockers);

        let mask = bishop_vision_mask(square);
        let shift = 64 - mask.count_ones();
        let magic = find_magic_number_for_square(&blockers, &attacks, shift);

        let table_size = 1 << mask.count_ones();
        let mut table = vec![0u64; table_size];

        for &b in &blockers {
            let idx = ((b & mask).wrapping_mul(magic)) >> shift;
            table[idx as usize] = bishop_attacks_per_square(square, b);
        }

        entries_vec.push(MagicEntry {
            magic,
            shift,
            table,
        });
    }

    let entries: [MagicEntry; 64] = entries_vec
        .try_into()
        .expect("Expected exactly 64 entries for magic table generation");

    return BishopMagicTables { entries };
}
