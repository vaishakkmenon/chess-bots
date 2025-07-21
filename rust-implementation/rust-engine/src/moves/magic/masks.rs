use crate::utils::enumerate_subsets;

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

#[cfg(test)]
mod tests {
    use super::*;

    fn bitboard_to_string(bb: u64) -> String {
        let mut s = String::new();
        for rank in (0..8).rev() {
            for file in 0..8 {
                let idx = rank * 8 + file;
                s.push(if (bb >> idx) & 1 == 1 { 'X' } else { '.' });
            }
            s.push('\n');
        }
        s
    }

    #[test]
    fn test_rook_vision_d4() {
        let idx = 3 * 8 + 3; // d4
        let mask = rook_vision_mask(idx);
        println!("Rook vision mask for d4:\n{}", bitboard_to_string(mask));
        assert_eq!(mask.count_ones(), 10); // was 14
    }

    #[test]
    fn test_bishop_vision_d4() {
        let idx = 3 * 8 + 3; // d4
        let mask = bishop_vision_mask(idx);
        println!("Bishop vision mask for d4:\n{}", bitboard_to_string(mask));
        assert_eq!(mask.count_ones(), 9); // was 13
    }

    #[test]
    fn test_rook_vision_a1() {
        let idx = 0; // a1
        let mask = rook_vision_mask(idx);
        println!("Rook vision mask for a1:\n{}", bitboard_to_string(mask));
        assert_eq!(mask.count_ones(), 12); // was 10
    }

    #[test]
    fn test_bishop_vision_h8() {
        let idx = 63; // h8
        let mask = bishop_vision_mask(idx);
        println!("Bishop vision mask for h8:\n{}", bitboard_to_string(mask));
        assert_eq!(mask.count_ones(), 6); // was 7
    }
}
