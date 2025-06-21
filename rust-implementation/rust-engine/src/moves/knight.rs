pub const KNIGHT_ATTACKS: [u64; 64] = [
    0x0000000000020400, // 0
    0x0000000000050800, // 1
    0x00000000000A1100, // 2
    0x0000000000142200, // 3
    0x0000000000284400, // 4
    0x0000000000508800, // 5
    0x0000000000A01000, // 6
    0x0000000000402000, // 7
    0x0000000002040004, // 8
    0x0000000005080008, // 9
    0x000000000A110011, // 10
    0x0000000014220022, // 11
    0x0000000028440044, // 12
    0x0000000050880088, // 13
    0x00000000A0100010, // 14
    0x0000000040200020, // 15
    0x0000000204000402, // 16
    0x0000000508000805, // 17
    0x0000000A1100110A, // 18
    0x0000001422002214, // 19
    0x0000002844004428, // 20
    0x0000005088008850, // 21
    0x000000A0100010A0, // 22
    0x0000004020002040, // 23
    0x0000020400040200, // 24
    0x0000050800080500, // 25
    0x00000A1100110A00, // 26
    0x0000142200221400, // 27
    0x0000284400442800, // 28
    0x0000508800885000, // 29
    0x0000A0100010A000, // 30
    0x0000402000204000, // 31
    0x0002040004020000, // 32
    0x0005080008050000, // 33
    0x000A1100110A0000, // 34
    0x0014220022140000, // 35
    0x0028440044280000, // 36
    0x0050880088500000, // 37
    0x00A0100010A00000, // 38
    0x0040200020400000, // 39
    0x0204000402000000, // 40
    0x0508000805000000, // 41
    0x0A1100110A000000, // 42
    0x1422002214000000, // 43
    0x2844004428000000, // 44
    0x5088008850000000, // 45
    0xA0100010A0000000, // 46
    0x4020002040000000, // 47
    0x0400040200000000, // 48
    0x0800080500000000, // 49
    0x1100110A00000000, // 50
    0x2200221400000000, // 51
    0x4400442800000000, // 52
    0x8800885000000000, // 53
    0x100010A000000000, // 54
    0x2000204000000000, // 55
    0x0004020000000000, // 56
    0x0008050000000000, // 57
    0x00110A0000000000, // 58
    0x0022140000000000, // 59
    0x0044280000000000, // 60
    0x0088500000000000, // 61
    0x0010A00000000000, // 62
    0x0020400000000000, // 63
];

pub fn print_bitboard(bb: u64) {
    for rank in (0..8).rev() {
        for file in 0..8 {
            let square = rank * 8 + file;
            let occupied = (bb >> square) & 1 != 0;
            print!("{} ", if occupied { 'X' } else { '.' });
        }
        println!("  {}", rank + 1);
    }
    println!("a b c d e f g h");
}

pub fn knight_attacks(square: u8) -> u64 {
    let rank = square / 8;
    let file = square % 8;

    let mut attacks = 0u64;

    let deltas: [(i8, i8); 8] = [
        (2, 1),
        (2, -1),
        (-2, 1),
        (-2, -1),
        (1, 2),
        (1, -2),
        (-1, 2),
        (-1, -2),
    ];

    for (dr, df) in deltas {
        let r = rank as i8 + dr;
        let f = file as i8 + df;
        if (0..8).contains(&r) && (0..8).contains(&f) {
            let dest = r * 8 + f;
            attacks |= 1u64 << dest;
        }
    }
    return attacks;
}

#[cfg(test)]
mod tests {
    use super::{KNIGHT_ATTACKS, knight_attacks};

    #[test]
    fn dump_knight_attacks() {
        for sq in 0..64 {
            println!("0x{:016X}, // {}", knight_attacks(sq), sq);
        }
    }

    fn assert_attacks(square: u8, expected: u64) {
        let generated = KNIGHT_ATTACKS[square as usize];
        assert_eq!(
            generated, expected,
            "Mismatch on square {}: expected {:016X}, got {:016X}",
            square, expected, generated
        );
    }

    #[test]
    fn test_knight_attacks_center() {
        let d4 = 3 + 8 * 3; // d4 = index 27
        let expected = 0x0000142200221400;
        assert_attacks(d4, expected);
    }

    #[test]
    fn test_knight_attacks_corner_a1() {
        let a1 = 0;
        let expected = 0x0000000000020400;
        assert_attacks(a1, expected);
    }

    #[test]
    fn test_knight_attacks_corner_h1() {
        let h1 = 7;
        let expected = 0x0000000000402000;
        assert_attacks(h1, expected);
    }

    #[test]
    fn test_knight_attacks_corner_a8() {
        let a8 = 56;
        let expected = 0x0004020000000000;
        assert_attacks(a8, expected);
    }

    #[test]
    fn test_knight_attacks_corner_h8() {
        let h8 = 63;
        let expected = 0x0020400000000000;
        assert_attacks(h8, expected);
    }

    #[test]
    fn test_knight_attacks_matches_reference_function() {
        for square in 0u8..64 {
            let expected = knight_attacks(square);
            let actual = KNIGHT_ATTACKS[square as usize];
            assert_eq!(
                expected, actual,
                "Mismatch at square {}: expected {:016X}, got {:016X}",
                square, expected, actual
            );
        }
    }
}
