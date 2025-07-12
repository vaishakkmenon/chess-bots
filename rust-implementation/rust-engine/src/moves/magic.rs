use crate::utils::enumerate_subsets;
use rand::random;
use std::collections::HashMap;

pub fn rook_vision_mask(square: usize) -> u64 {
    let rank = square / 8;
    let file = square % 8;
    let mut mask = 0u64;

    for r in (rank + 1)..7 {
        let sq = r * 8 + file;
        mask |= 1u64 << sq;
    }

    for r in (1..rank).rev() {
        let sq = r * 8 + file;
        mask |= 1u64 << sq;
    }

    for f in (file + 1)..7 {
        let sq = rank * 8 + f;
        mask |= 1u64 << sq;
    }

    for f in (1..file).rev() {
        let sq = rank * 8 + f;
        mask |= 1u64 << sq;
    }

    return mask;
}

pub fn bishop_vision_mask(square: usize) -> u64 {
    let rank = square / 8;
    let file = square % 8;
    let mut mask = 0u64;

    // NE
    let mut r = rank + 1;
    let mut f = file + 1;
    while r <= 6 && f <= 6 {
        let sq = r * 8 + f;
        mask |= 1u64 << sq;
        r += 1;
        f += 1;
    }

    // SW
    if let Some(mut r) = rank.checked_sub(1) {
        if let Some(mut f) = file.checked_sub(1) {
            while r >= 1 && f >= 1 {
                let sq = r * 8 + f;
                mask |= 1u64 << sq;
                r -= 1;
                f -= 1;
            }
        }
    }

    // NW
    let mut r = rank + 1;
    if let Some(mut f) = file.checked_sub(1) {
        while r <= 6 && f >= 1 {
            let sq = r * 8 + f;
            mask |= 1u64 << sq;
            r += 1;
            f -= 1;
        }
    }

    // SE
    if let Some(mut r) = rank.checked_sub(1) {
        let mut f = file + 1;
        while r >= 1 && f <= 6 {
            let sq = r * 8 + f;
            mask |= 1u64 << sq;
            r -= 1;
            f += 1;
        }
    }

    mask
}

pub fn generate_rook_blockers(square: usize) -> Vec<u64> {
    let mask = rook_vision_mask(square);
    let mut configs = Vec::new();

    enumerate_subsets(mask, |subset| {
        configs.push(subset);
    });

    return configs;
}

pub fn generate_bishop_blockers(square: usize) -> Vec<u64> {
    let mask = bishop_vision_mask(square);
    let mut configs = Vec::new();

    enumerate_subsets(mask, |subset| {
        configs.push(subset);
    });

    return configs;
}

pub fn rook_attacks_per_square(square: usize, blockers: u64) -> u64 {
    let rank = square / 8;
    let file = square % 8;
    let mut attacks = 0u64;

    // North
    let mut r = rank + 1;
    while r <= 7 {
        let sq = r * 8 + file;
        attacks |= 1u64 << sq;
        if (blockers >> sq) & 1 != 0 {
            break;
        }
        r += 1;
    }

    // South
    if let Some(mut r) = rank.checked_sub(1) {
        while r <= 7 {
            let sq = r * 8 + file;
            attacks |= 1u64 << sq;
            if (blockers >> sq) & 1 != 0 {
                break;
            }
            if r == 0 {
                break;
            }
            r -= 1;
        }
    }

    // East
    let mut f = file + 1;
    while f <= 7 {
        let sq = rank * 8 + f;
        attacks |= 1u64 << sq;
        if (blockers >> sq) & 1 != 0 {
            break;
        }
        f += 1;
    }

    // West
    if let Some(mut f) = file.checked_sub(1) {
        while f <= 7 {
            let sq = rank * 8 + f;
            attacks |= 1u64 << sq;
            if (blockers >> sq) & 1 != 0 {
                break;
            }
            if f == 0 {
                break;
            }
            f -= 1;
        }
    }

    return attacks;
}

pub fn bishop_attacks_per_square(square: usize, blockers: u64) -> u64 {
    let rank = square / 8;
    let file = square % 8;
    let mut attacks = 0u64;

    // NE
    let mut r = rank + 1;
    let mut f = file + 1;
    while r <= 7 && f <= 7 {
        let sq = r * 8 + f;
        attacks |= 1u64 << sq;
        if (blockers >> sq) & 1 != 0 {
            break;
        }
        r += 1;
        f += 1;
    }

    // SW
    if let Some(mut r) = rank.checked_sub(1) {
        if let Some(mut f) = file.checked_sub(1) {
            loop {
                let sq = r * 8 + f;
                attacks |= 1u64 << sq;
                if (blockers >> sq) & 1 != 0 {
                    break;
                }
                if r == 0 || f == 0 {
                    break;
                }
                r -= 1;
                f -= 1;
            }
        }
    }

    // NW
    let mut r = rank + 1;
    if let Some(mut f) = file.checked_sub(1) {
        while r <= 7 {
            let sq = r * 8 + f;
            attacks |= 1u64 << sq;
            if (blockers >> sq) & 1 != 0 {
                break;
            }
            r += 1;
            if f == 0 {
                break;
            }
            f -= 1;
        }
    }

    // SE
    if let Some(mut r) = rank.checked_sub(1) {
        let mut f = file + 1;
        while f <= 7 {
            let sq = r * 8 + f;
            attacks |= 1u64 << sq;
            if (blockers >> sq) & 1 != 0 {
                break;
            }
            if r == 0 {
                break;
            }
            r -= 1;
            f += 1;
        }
    }

    return attacks;
}

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

pub fn get_rook_attack_bitboards(square: usize, blockers: &[u64]) -> Vec<u64> {
    blockers
        .iter()
        .map(|&b| rook_attacks_per_square(square, b))
        .collect()
}

pub fn get_bishop_attack_bitboards(square: usize, blockers: &[u64]) -> Vec<u64> {
    blockers
        .iter()
        .map(|&b| bishop_attacks_per_square(square, b))
        .collect()
}

pub fn is_magic_candidate_valid(blockers: &[u64], attacks: &[u64], magic: u64, shift: u32) -> bool {
    let mut seen: HashMap<u64, u64> = HashMap::new();

    for i in 0..blockers.len() {
        let blocker = blockers[i];
        let attack = attacks[i];
        let product = blocker.wrapping_mul(magic);
        let index = product >> shift;

        if seen.contains_key(&index) {
            let existing_attack = seen[&index];
            if existing_attack != attack {
                return false;
            }
        } else {
            seen.insert(index, attack);
        }
    }

    return true;
}

pub fn find_magic_number_for_square(blockers: &[u64], attacks: &[u64], shift: u32) -> u64 {
    for attempt in 0..1_000_000 {
        let magic = random::<u64>() & random::<u64>() & random::<u64>();

        if is_magic_candidate_valid(blockers, attacks, magic, shift) {
            println!(
                "Found magic number after {} attempts: {:#018x}",
                attempt + 1,
                magic
            );
            return magic;
        }
    }

    panic!("Failed to find a valid magic number after 1,000,000 attempts");
}
