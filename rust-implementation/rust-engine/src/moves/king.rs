/// Precomputed king attack bitboards for each square.
pub const KING_ATTACKS: [u64; 64] = [
    0x0000000000000302, // 0
    0x0000000000000705, // 1
    0x0000000000000E0A, // 2
    0x0000000000001C14, // 3
    0x0000000000003828, // 4
    0x0000000000007050, // 5
    0x000000000000E0A0, // 6
    0x000000000000C040, // 7
    0x0000000000030203, // 8
    0x0000000000070507, // 9
    0x00000000000E0A0E, // 10
    0x00000000001C141C, // 11
    0x0000000000382838, // 12
    0x0000000000705070, // 13
    0x0000000000E0A0E0, // 14
    0x0000000000C040C0, // 15
    0x0000000003020300, // 16
    0x0000000007050700, // 17
    0x000000000E0A0E00, // 18
    0x000000001C141C00, // 19
    0x0000000038283800, // 20
    0x0000000070507000, // 21
    0x00000000E0A0E000, // 22
    0x00000000C040C000, // 23
    0x0000000302030000, // 24
    0x0000000705070000, // 25
    0x0000000E0A0E0000, // 26
    0x0000001C141C0000, // 27
    0x0000003828380000, // 28
    0x0000007050700000, // 29
    0x000000E0A0E00000, // 30
    0x000000C040C00000, // 31
    0x0000030203000000, // 32
    0x0000070507000000, // 33
    0x00000E0A0E000000, // 34
    0x00001C141C000000, // 35
    0x0000382838000000, // 36
    0x0000705070000000, // 37
    0x0000E0A0E0000000, // 38
    0x0000C040C0000000, // 39
    0x0003020300000000, // 40
    0x0007050700000000, // 41
    0x000E0A0E00000000, // 42
    0x001C141C00000000, // 43
    0x0038283800000000, // 44
    0x0070507000000000, // 45
    0x00E0A0E000000000, // 46
    0x00C040C000000000, // 47
    0x0302030000000000, // 48
    0x0705070000000000, // 49
    0x0E0A0E0000000000, // 50
    0x1C141C0000000000, // 51
    0x3828380000000000, // 52
    0x7050700000000000, // 53
    0xE0A0E00000000000, // 54
    0xC040C00000000000, // 55
    0x0203000000000000, // 56
    0x0507000000000000, // 57
    0x0A0E000000000000, // 58
    0x141C000000000000, // 59
    0x2838000000000000, // 60
    0x5070000000000000, // 61
    0xA0E0000000000000, // 62
    0x40C0000000000000, // 63
];

/// Computes the king's attack mask from a given square (0..63).
pub fn king_attacks(square: u8) -> u64 {
    let rank = square / 8;
    let file = square % 8;
    let mut attacks = 0u64;

    for dr in -1..=1 {
        for df in -1..=1 {
            if dr == 0 && df == 0 {
                continue;
            }
            let r = rank as i8 + dr;
            let f = file as i8 + df;
            if (0..8).contains(&r) && (0..8).contains(&f) {
                let dest = r * 8 + f;
                attacks |= 1u64 << dest;
            }
        }
    }
    attacks
}

#[cfg(test)]
mod tests {
    // use super::{KING_ATTACKS, king_attacks};
    use super::{KING_ATTACKS, king_attacks};

    #[test]
    fn dump_king_attacks() {
        for sq in 0..64 {
            println!("0x{:016X}, // {}", king_attacks(sq), sq);
        }
    }

    fn assert_attacks(square: u8, expected: u64) {
        let actual = KING_ATTACKS[square as usize];
        assert_eq!(
            actual, expected,
            "Mismatch at square {}: expected {:016X}, got {:016X}",
            square, expected, actual
        );
    }

    #[test]
    fn test_king_attacks_center() {
        let d4 = 3 + 8 * 3; // index 27
        let expected = 0x0000001C141C0000;
        assert_attacks(d4, expected);
    }

    #[test]
    fn test_king_attacks_corner_a1() {
        let a1 = 0;
        let expected = king_attacks(a1);
        assert_attacks(a1, expected);
    }

    #[test]
    fn test_king_attacks_corner_h1() {
        let h1 = 7;
        let expected = king_attacks(h1);
        assert_attacks(h1, expected);
    }

    #[test]
    fn test_king_attacks_corner_a8() {
        let a8 = 56;
        let expected = king_attacks(a8);
        assert_attacks(a8, expected);
    }

    #[test]
    fn test_king_attacks_corner_h8() {
        let h8 = 63;
        let expected = king_attacks(h8);
        assert_attacks(h8, expected);
    }

    #[test]
    fn test_king_attacks_matches_reference_function() {
        for square in 0u8..64 {
            let expected = king_attacks(square);
            let actual = KING_ATTACKS[square as usize];
            assert_eq!(
                expected, actual,
                "Mismatch at square {}: expected {:016X}, got {:016X}",
                square, expected, actual
            );
        }
    }
}
