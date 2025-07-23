use crate::utils::square_index;

#[inline]
pub fn rook_attacks_per_square(square: usize, blockers: u64) -> u64 {
    let rank = square / 8;
    let file = square % 8;
    let mut attacks = 0u64;

    // North
    let mut r = rank + 1;
    while r <= 7 {
        let sq = square_index(r, file);
        attacks |= 1u64 << sq;
        if (blockers >> sq) & 1 != 0 {
            break;
        }
        r += 1;
    }

    // South
    if let Some(mut r) = rank.checked_sub(1) {
        while r <= 7 {
            let sq = square_index(r, file);
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

#[inline]
pub fn bishop_attacks_per_square(square: usize, blockers: u64) -> u64 {
    let rank = square / 8;
    let file = square % 8;
    let mut attacks = 0u64;

    // NE
    let mut r = rank + 1;
    let mut f = file + 1;
    while r <= 7 && f <= 7 {
        let sq = square_index(r, f);
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
                let sq = square_index(r, f);
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
            let sq = square_index(r, f);
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
            let sq = square_index(r, f);
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

#[cfg(test)]
mod tests {
    use super::*;

    fn bit(sq: usize) -> u64 {
        1u64 << sq
    }

    #[test]
    fn rook_attacks_from_d4_no_blockers() {
        let square = 27; // d4
        let blockers = 0;
        let result = rook_attacks_per_square(square, blockers);

        let expected = bit(3)   // d1
            | bit(11)           // d2
            | bit(19)           // d3
            | bit(35)           // d5
            | bit(43)           // d6
            | bit(51)           // d7
            | bit(59)           // d8
            | bit(24)           // a4
            | bit(25)           // b4
            | bit(26)           // c4
            | bit(28)           // e4
            | bit(29)           // f4
            | bit(30)           // g4
            | bit(31); // h4

        assert_eq!(result, expected);
    }

    #[test]
    fn bishop_attacks_from_d4_no_blockers() {
        let square = 27; // d4
        let blockers = 0;
        let result = bishop_attacks_per_square(square, blockers);

        let expected = bit(36) // e5
            | bit(45)          // f6
            | bit(54)          // g7
            | bit(63)          // h8 
            | bit(34)          // c5  NW
            | bit(41)          // b6  NW
            | bit(48)          // a7  NW
            | bit(20)          // e3
            | bit(13)          // f2
            | bit(6)           // g1
            | bit(18)          // c3
            | bit(9)           // b2
            | bit(0); // a1

        assert_eq!(result, expected);
    }

    #[test]
    fn rook_attacks_blocked_east() {
        let square = 27; // d4
        let blockers = bit(28); // e4 blocks east
        let result = rook_attacks_per_square(square, blockers);

        let expected = bit(3)   // d1
            | bit(11)           // d2
            | bit(19)           // d3
            | bit(35)           // d5
            | bit(43)           // d6
            | bit(51)           // d7
            | bit(59)           // d8
            | bit(24)           // a4
            | bit(25)           // b4
            | bit(26)           // c4
            | bit(28); // e4 (included)

        assert_eq!(result, expected);
    }

    #[test]
    fn bishop_attacks_blocked_ne() {
        let square = 27; // d4
        let blockers = bit(36); // e5 blocks NE
        let result = bishop_attacks_per_square(square, blockers);

        let expected = bit(36) // e5 (included)
            | bit(20)          // e3
            | bit(13)          // f2
            | bit(6)           // g1
            | bit(18)          // c3
            | bit(9)           // b2
            | bit(0)           // a1
            | bit(34)          // c5 
            | bit(41)          // b6 
            | bit(48); // a7 

        assert_eq!(result, expected);
    }
}
