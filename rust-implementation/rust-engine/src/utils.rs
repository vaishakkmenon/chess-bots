pub fn enumerate_subsets<F>(mask: u64, mut f: F)
where
    F: FnMut(u64),
{
    let mut subset = mask;
    loop {
        f(subset);
        if subset == 0 {
            break;
        }
        subset = (subset - 1) & mask;
    }
}

/// Calculates a squares index in the bitboard
#[inline(always)]
pub const fn square_index(rank: usize, file: usize) -> usize {
    rank * 8 + file
}

/// Converts a bitboard into a printable 8x8 board view for debugging.
pub fn bitboard_to_string(bb: u64) -> String {
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
