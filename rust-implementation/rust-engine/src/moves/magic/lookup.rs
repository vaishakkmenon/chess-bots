use super::masks::*;

pub fn rook_attacks(
    square: usize,
    occupied: u64,
    magic: u64,
    shift: u32,
    attack_table: &[u64],
) -> u64 {
    let blockers = occupied & rook_vision_mask(square);
    let index = (blockers.wrapping_mul(magic)) >> shift;
    attack_table[index as usize]
}

pub fn bishop_attacks(
    square: usize,
    occupied: u64,
    magic: u64,
    shift: u32,
    attack_table: &[u64],
) -> u64 {
    let blockers = occupied & bishop_vision_mask(square);
    let index = (blockers.wrapping_mul(magic)) >> shift;
    attack_table[index as usize]
}

pub fn queen_attacks(
    square: usize,
    occupied: u64,
    rook_magic: u64,
    rook_shift: u32,
    rook_table: &[u64],
    bishop_magic: u64,
    bishop_shift: u32,
    bishop_table: &[u64],
) -> u64 {
    let rook = rook_attacks(square, occupied, rook_magic, rook_shift, rook_table);
    let bishop = bishop_attacks(square, occupied, bishop_magic, bishop_shift, bishop_table);
    rook | bishop
}
