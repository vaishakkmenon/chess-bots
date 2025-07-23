use rust_engine::moves::magic::{
    bishop_attacks, bishop_attacks_per_square, bishop_vision_mask, find_magic_number_for_square,
    generate_bishop_blockers, generate_rook_blockers, get_bishop_attack_bitboards,
    get_rook_attack_bitboards, is_magic_candidate_valid, precompute_bishop_attacks,
    precompute_rook_attacks, queen_attacks, rook_attacks, rook_attacks_per_square,
    rook_vision_mask,
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
fn test_rook_vision_d4() {
    let d4 = 3 + 3 * 8;
    let mask = rook_vision_mask(d4);
    println!("Rook vision mask d4:");
    print_bitboard(mask);
}

#[test]
fn test_rook_vision_a1() {
    let a1 = 0;
    let mask = rook_vision_mask(a1);
    println!("Rook vision mask a1:");
    print_bitboard(mask);
}

#[test]
fn test_bishop_vision_d4() {
    let d4 = 3 + 3 * 8;
    let mask = bishop_vision_mask(d4);
    println!("Bishop vision mask d4:");
    print_bitboard(mask);
}

#[test]
fn test_bishop_vision_c1() {
    let c1 = 2;
    let mask = bishop_vision_mask(c1);
    println!("Bishop vision mask c1:");
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
        let mask = rook_vision_mask(square);
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
        let mask = bishop_vision_mask(square);
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
fn test_invalid_magic_detects_collisions() {
    let d4 = 3 + 3 * 8;
    let blockers = generate_rook_blockers(d4);
    let attacks = get_rook_attack_bitboards(d4, &blockers);

    // This magic number is almost certainly invalid
    let bad_magic = 1u64;

    let shift = 64 - rook_vision_mask(d4).count_ones();

    let valid = is_magic_candidate_valid(&blockers, &attacks, bad_magic, shift);
    assert!(!valid, "Expected invalid magic to produce collisions");
}

#[test]
fn test_trivial_magic_zero_fails() {
    let d4 = 3 + 3 * 8;
    let blockers = generate_rook_blockers(d4);
    let attacks = get_rook_attack_bitboards(d4, &blockers);

    // Trivial magic number zero is invalid
    let bad_magic = 0u64;

    let shift = 64 - rook_vision_mask(d4).count_ones();

    let valid = is_magic_candidate_valid(&blockers, &attacks, bad_magic, shift);
    assert!(!valid, "Magic 0 must be invalid");
}

#[test]
fn test_all_same_attack_always_valid() {
    let d4 = 3 + 3 * 8;
    let blockers = generate_rook_blockers(d4);

    // If all attacks are identical, any magic is "valid"
    let attacks = vec![0xDEADBEEF; blockers.len()];

    let shift = 64 - rook_vision_mask(d4).count_ones();

    let magic = 1u64;
    let valid = is_magic_candidate_valid(&blockers, &attacks, magic, shift);
    assert!(
        valid,
        "If all attacks are identical, any magic must be valid"
    );
}

#[test]
fn test_invalid_bishop_magic_detects_collisions() {
    let d4 = 3 + 3 * 8;
    let blockers = generate_bishop_blockers(d4);
    let attacks = get_bishop_attack_bitboards(d4, &blockers);

    // Almost certainly invalid
    let bad_magic = 1u64;

    let shift = 64 - bishop_vision_mask(d4).count_ones();

    let valid = is_magic_candidate_valid(&blockers, &attacks, bad_magic, shift);
    assert!(
        !valid,
        "Expected invalid bishop magic to produce collisions"
    );
}

#[test]
fn test_trivial_bishop_magic_zero_fails() {
    let d4 = 3 + 3 * 8;
    let blockers = generate_bishop_blockers(d4);
    let attacks = get_bishop_attack_bitboards(d4, &blockers);

    let bad_magic = 0u64;
    let shift = 64 - bishop_vision_mask(d4).count_ones();

    let valid = is_magic_candidate_valid(&blockers, &attacks, bad_magic, shift);
    assert!(!valid, "Magic 0 must be invalid");
}

#[test]
fn test_bishop_all_same_attack_always_valid() {
    let d4 = 3 + 3 * 8;
    let blockers = generate_bishop_blockers(d4);

    // All identical attacks: any magic passes
    let attacks = vec![0xDEADBEEF; blockers.len()];

    let shift = 64 - bishop_vision_mask(d4).count_ones();
    let magic = 1u64;

    let valid = is_magic_candidate_valid(&blockers, &attacks, magic, shift);
    assert!(
        valid,
        "If all attacks are identical, any magic must be valid"
    );
}

#[test]
fn test_find_magic_for_rook_d4_real_search() -> Result<(), String> {
    let d4 = 3 + 3 * 8;
    let blockers = generate_rook_blockers(d4);
    let attacks = get_rook_attack_bitboards(d4, &blockers);
    let shift = 64 - rook_vision_mask(d4).count_ones();

    let magic = find_magic_number_for_square(&blockers, &attacks, shift)?;
    let valid = is_magic_candidate_valid(&blockers, &attacks, magic, shift);
    assert!(valid, "The found rook magic must be valid");

    Ok(())
}

#[test]
fn test_find_magic_for_bishop_d4_real_search() -> Result<(), String> {
    let d4 = 3 + 3 * 8;
    let blockers = generate_bishop_blockers(d4);
    let attacks = get_bishop_attack_bitboards(d4, &blockers);
    let shift = 64 - bishop_vision_mask(d4).count_ones();

    let magic = find_magic_number_for_square(&blockers, &attacks, shift)?;
    let valid = is_magic_candidate_valid(&blockers, &attacks, magic, shift);
    assert!(valid, "The found bishop magic must be valid");

    Ok(())
}

#[test]
fn test_runtime_rook_attacks_matches_per_square() -> Result<(), String> {
    let d4 = 3 + 3 * 8;
    let blockers = generate_rook_blockers(d4);
    let attacks = get_rook_attack_bitboards(d4, &blockers);
    let shift = 64 - rook_vision_mask(d4).count_ones();
    let magic = find_magic_number_for_square(&blockers, &attacks, shift)?;

    let mut table = vec![0u64; attacks.len()];
    for (i, &b) in blockers.iter().enumerate() {
        let idx = (b.wrapping_mul(magic)) >> shift;
        table[idx as usize] = attacks[i];
    }

    for (i, &b) in blockers.iter().enumerate() {
        let expected = attacks[i];
        let lookup = rook_attacks(d4, b, magic, shift, &table);
        assert_eq!(lookup, expected, "Mismatch for blocker subset {}", i);
    }

    Ok(())
}

#[test]
fn test_runtime_bishop_attacks_matches_per_square() -> Result<(), String> {
    let d4 = 3 + 3 * 8;
    let blockers = generate_bishop_blockers(d4);
    let attacks = get_bishop_attack_bitboards(d4, &blockers);
    let shift = 64 - bishop_vision_mask(d4).count_ones();
    let magic = find_magic_number_for_square(&blockers, &attacks, shift)?;

    let mut table = vec![0u64; attacks.len()];
    for (i, &b) in blockers.iter().enumerate() {
        let idx = (b.wrapping_mul(magic)) >> shift;
        table[idx as usize] = attacks[i];
    }

    for (i, &b) in blockers.iter().enumerate() {
        let expected = attacks[i];
        let lookup = bishop_attacks(d4, b, magic, shift, &table);
        assert_eq!(lookup, expected, "Mismatch for blocker subset {}", i);
    }

    Ok(())
}

#[test]
fn test_runtime_queen_attacks_matches_per_square() -> Result<(), String> {
    let d4 = 3 + 3 * 8;

    let rook_blockers = generate_rook_blockers(d4);
    let rook_attacks_vec = get_rook_attack_bitboards(d4, &rook_blockers);
    let rook_shift = 64 - rook_vision_mask(d4).count_ones();
    let rook_magic = find_magic_number_for_square(&rook_blockers, &rook_attacks_vec, rook_shift)?;

    let mut rook_table = vec![0u64; rook_attacks_vec.len()];
    for (i, &b) in rook_blockers.iter().enumerate() {
        let idx = (b.wrapping_mul(rook_magic)) >> rook_shift;
        rook_table[idx as usize] = rook_attacks_vec[i];
    }

    let bishop_blockers = generate_bishop_blockers(d4);
    let bishop_attacks_vec = get_bishop_attack_bitboards(d4, &bishop_blockers);
    let bishop_shift = 64 - bishop_vision_mask(d4).count_ones();
    let bishop_magic =
        find_magic_number_for_square(&bishop_blockers, &bishop_attacks_vec, bishop_shift)?;

    let mut bishop_table = vec![0u64; bishop_attacks_vec.len()];
    for (i, &b) in bishop_blockers.iter().enumerate() {
        let idx = (b.wrapping_mul(bishop_magic)) >> bishop_shift;
        bishop_table[idx as usize] = bishop_attacks_vec[i];
    }

    let occupied = 0;
    let queen = queen_attacks(
        d4,
        occupied,
        rook_magic,
        rook_shift,
        &rook_table,
        bishop_magic,
        bishop_shift,
        &bishop_table,
    );

    let expected = rook_attacks_per_square(d4, occupied) | bishop_attacks_per_square(d4, occupied);

    assert_eq!(queen, expected, "Queen attacks should match rook | bishop");

    Ok(())
}
