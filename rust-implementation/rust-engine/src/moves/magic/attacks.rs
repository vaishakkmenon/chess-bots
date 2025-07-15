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
