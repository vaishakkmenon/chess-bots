use crate::utils::enumerate_subsets;

pub fn rook_occupancy_mask(square: usize) -> u64 {
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

pub fn bishop_occupancy_mask(square: usize) -> u64 {
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
    r = rank.wrapping_sub(1);
    f = file.wrapping_sub(1);
    while r >= 1 && f >= 1 {
        let sq = r * 8 + f;
        mask |= 1u64 << sq;
        r -= 1;
        f -= 1;
    }

    // NW
    r = rank + 1;
    f = file.wrapping_sub(1);
    while r <= 6 && f >= 1 {
        let sq = r * 8 + f;
        mask |= 1u64 << sq;
        r += 1;
        f -= 1;
    }

    // SE
    r = rank.wrapping_sub(1);
    f = file + 1;
    while r >= 1 && f <= 6 {
        let sq = r * 8 + f;
        mask |= 1u64 << sq;
        r -= 1;
        f += 1;
    }

    return mask;
}

pub fn generate_rook_blockers(square: usize) -> Vec<u64> {
    let mask = rook_occupancy_mask(square);
    let mut configs = Vec::new();

    enumerate_subsets(mask, |subset| {
        configs.push(subset);
    });

    return configs;
}

pub fn generate_bishop_blockers(square: usize) -> Vec<u64> {
    let mask = bishop_occupancy_mask(square);
    let mut configs = Vec::new();

    enumerate_subsets(mask, |subset| {
        configs.push(subset);
    });

    return configs;
}

#[cfg(test)]
mod tests {

    use super::{
        bishop_occupancy_mask, generate_bishop_blockers, generate_rook_blockers,
        rook_occupancy_mask,
    };

    fn print_bitboard(mask: u64) {
        for rank in (0..8).rev() {
            for file in 0..8 {
                let sq = rank * 8 + file;
                let is_set = (mask >> sq) & 1;
                if is_set == 1 {
                    let file_char = (b'a' + file as u8) as char;
                    let rank_char = (b'1' + rank as u8) as char;
                    print!("{}{} ", file_char, rank_char);
                }
            }
        }
        println!();
    }

    #[test]
    fn test_rook_mask_d4() {
        let d4 = 3 + 3 * 8; // square 27
        let mask = rook_occupancy_mask(d4);
        print_bitboard(mask);
    }

    #[test]
    fn test_bishop_mask_d4() {
        let d4 = 3 + 3 * 8; // square 27
        let mask = bishop_occupancy_mask(d4);
        print_bitboard(mask);
    }

    #[test]
    fn test_rook_blockers_d4() {
        let d4 = 3 + 3 * 8;
        let configs = generate_rook_blockers(d4);
        println!("Total configs: {}", configs.len());
        // for (i, b) in configs.iter().enumerate() {
        //     println!("Config {}:", i);
        //     print_bitboard(*b);
        // }
    }

    #[test]
    fn test_bishop_blockers_d4() {
        let d4 = 3 + 3 * 8;
        let configs = generate_bishop_blockers(d4);
        println!("Total configs: {}", configs.len());
        // for (i, b) in configs.iter().enumerate() {
        //     println!("Config {}:", i);
        //     print_bitboard(*b);
        // }
    }
}
