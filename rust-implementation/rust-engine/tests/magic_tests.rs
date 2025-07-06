use rust_engine::moves::magic::{
    bishop_attacks_per_square, bishop_occupancy_mask, generate_bishop_blockers,
    generate_rook_blockers, precompute_bishop_attacks, precompute_rook_attacks,
    rook_attacks_per_square, rook_occupancy_mask,
};

/// Helper: Pretty-print a bitboard
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
fn test_rook_occupancy_d4() {
    let d4 = 3 + 3 * 8;
    let mask = rook_occupancy_mask(d4);
    println!("Rook occupancy mask d4:");
    print_bitboard(mask);
}

#[test]
fn test_rook_occupancy_a1() {
    let a1 = 0;
    let mask = rook_occupancy_mask(a1);
    println!("Rook occupancy mask a1:");
    print_bitboard(mask);
}

#[test]
fn test_bishop_occupancy_d4() {
    let d4 = 3 + 3 * 8;
    let mask = bishop_occupancy_mask(d4);
    println!("Bishop occupancy mask d4:");
    print_bitboard(mask);
}

#[test]
fn test_bishop_occupancy_c1() {
    let c1 = 2;
    let mask = bishop_occupancy_mask(c1);
    println!("Bishop occupancy mask c1:");
    print_bitboard(mask);
}

#[test]
fn test_rook_blocker_count_d4() {
    let d4 = 3 + 3 * 8;
    let blockers = generate_rook_blockers(d4);
    assert_eq!(blockers.len(), 1024);
}

#[test]
fn test_bishop_blocker_count_d4() {
    let d4 = 3 + 3 * 8;
    let blockers = generate_bishop_blockers(d4);
    assert_eq!(blockers.len(), 512);
}

#[test]
fn test_rook_attacks_no_blockers_d4() {
    let d4 = 3 + 3 * 8;
    let attacks = rook_attacks_per_square(d4, 0);
    println!("Rook attacks no blockers d4:");
    print_bitboard(attacks);
}

#[test]
fn test_rook_attacks_blockers_d4() {
    let d4 = 3 + 3 * 8;
    let blocker_d6 = (5 * 8) + 3;
    let blocker_f4 = (3 * 8) + 5;
    let blockers = (1u64 << blocker_d6) | (1u64 << blocker_f4);

    let attacks = rook_attacks_per_square(d4, blockers);
    println!("Rook attacks with blockers on d6 and f4:");
    print_bitboard(attacks);
}

#[test]
fn test_bishop_attacks_no_blockers_d4() {
    let d4 = 3 + 3 * 8;
    let attacks = bishop_attacks_per_square(d4, 0);
    println!("Bishop attacks no blockers d4:");
    print_bitboard(attacks);
}

#[test]
fn test_bishop_attacks_blockers_d4() {
    let d4 = 3 + 3 * 8;
    let blocker_f6 = (5 * 8) + 5;
    let blockers = 1u64 << blocker_f6;

    let attacks = bishop_attacks_per_square(d4, blockers);
    println!("Bishop attacks with blocker on f6:");
    print_bitboard(attacks);
}

#[test]
fn test_rook_attacks_no_blockers_a1() {
    let a1 = 0;
    let attacks = rook_attacks_per_square(a1, 0);
    println!("Rook attacks no blockers a1:");
    print_bitboard(attacks);
}

#[test]
fn test_bishop_attacks_no_blockers_c1() {
    let c1 = 2;
    let attacks = bishop_attacks_per_square(c1, 0);
    println!("Bishop attacks no blockers c1:");
    print_bitboard(attacks);
}

#[test]
fn test_rook_blocker_count_a1() {
    let a1 = 0;
    let blockers = generate_rook_blockers(a1);
    assert_eq!(blockers.len(), 4096);
}

#[test]
fn test_bishop_blocker_count_c1() {
    let c1 = 2;
    let blockers = generate_bishop_blockers(c1);
    println!("Bishop blocker count c1: {}", blockers.len());
}

#[test]
fn test_rook_attacks_blockers_first_square() {
    let d4 = 3 + 3 * 8;

    let blocker_north = (4 * 8) + 3; // d5
    let blocker_south = (2 * 8) + 3; // d3
    let blocker_east = (3 * 8) + 4; // e4
    let blocker_west = (3 * 8) + 2; // c4

    let blockers = (1u64 << blocker_north)
        | (1u64 << blocker_south)
        | (1u64 << blocker_east)
        | (1u64 << blocker_west);

    let attacks = rook_attacks_per_square(d4, blockers);
    println!("Rook attacks with blockers in first square each direction:");
    print_bitboard(attacks);
}

#[test]
fn test_bishop_attacks_blockers_first_square() {
    let d4 = 3 + 3 * 8;

    let blocker_ne = (4 * 8) + 4; // e5
    let blocker_nw = (4 * 8) + 2; // c5
    let blocker_se = (2 * 8) + 4; // e3
    let blocker_sw = (2 * 8) + 2; // c3

    let blockers =
        (1u64 << blocker_ne) | (1u64 << blocker_nw) | (1u64 << blocker_se) | (1u64 << blocker_sw);

    let attacks = bishop_attacks_per_square(d4, blockers);
    println!("Bishop attacks with blockers in first square each diagonal:");
    print_bitboard(attacks);
}

#[test]
fn test_rook_attack_table_counts() {
    let table = precompute_rook_attacks();

    for square in 0..64 {
        let mask = rook_occupancy_mask(square);
        let bit_count = mask.count_ones();
        let expected_len = 1 << bit_count;

        assert_eq!(
            table[square].len(),
            expected_len as usize,
            "Square {}: expected {} entries, got {}",
            square,
            expected_len,
            table[square].len()
        );
    }
}

#[test]
fn test_bishop_attack_table_counts() {
    let table = precompute_bishop_attacks();

    for square in 0..64 {
        let mask = bishop_occupancy_mask(square);
        let bit_count = mask.count_ones();
        let expected_len = 1 << bit_count;

        assert_eq!(
            table[square].len(),
            expected_len as usize,
            "Square {}: expected {} entries, got {}",
            square,
            expected_len,
            table[square].len()
        );
    }
}
