use crate::board::{Board, Color, Piece};

const P: i32 = 100;
const N: i32 = 320;
const B: i32 = 330;
const R: i32 = 500;
const Q: i32 = 900;

#[cfg(feature = "psqt")]
// Helper to mirror file
#[inline(always)]
pub fn mirror_vert(sq: u8) -> u8 {
    let file = sq & 7;
    let rank = sq >> 3;
    (file | ((7 - rank) << 3)) as u8
}

#[cfg(feature = "psqt")]
mod psqt_tables {
    pub const PAWN: [i16; 64] = [0; 64];
    pub const KNIGHT: [i16; 64] = [0; 64];
    pub const BISHOP: [i16; 64] = [0; 64];
    pub const ROOK: [i16; 64] = [0; 64];
    pub const QUEEN: [i16; 64] = [0; 64];
}

/// Material-only evaluation (White perspective), side-to-move agnostic.
/// Kings are excluded (value = 0). P=100, N=320, B=330, R=500, Q=900.
pub fn eval_material(board: &Board) -> i32 {
    let wp = board.pieces(Piece::Pawn, Color::White).count_ones();
    let bp = board.pieces(Piece::Pawn, Color::Black).count_ones();
    let wn = board.pieces(Piece::Knight, Color::White).count_ones();
    let bn = board.pieces(Piece::Knight, Color::Black).count_ones();
    let wb = board.pieces(Piece::Bishop, Color::White).count_ones();
    let bb = board.pieces(Piece::Bishop, Color::Black).count_ones();
    let wr = board.pieces(Piece::Rook, Color::White).count_ones();
    let br = board.pieces(Piece::Rook, Color::Black).count_ones();
    let wq = board.pieces(Piece::Queen, Color::White).count_ones();
    let bq = board.pieces(Piece::Queen, Color::Black).count_ones();

    let score: i32 = P * (wp as i32 - bp as i32)
        + N * (wn as i32 - bn as i32)
        + B * (wb as i32 - bb as i32)
        + R * (wr as i32 - br as i32)
        + Q * (wq as i32 - bq as i32);

    score
}

#[cfg(feature = "psqt")]
pub fn eval_psqt(board: &Board) -> i32 {
    use crate::utils::pop_lsb;
    use psqt_tables::*;
    let mut score: i32 = 0;

    let mut bb = board.bb(Color::White, Piece::Pawn);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score += PAWN[sq as usize] as i32;
    }

    let mut bb = board.bb(Color::White, Piece::Knight);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score += KNIGHT[sq as usize] as i32;
    }

    let mut bb = board.bb(Color::White, Piece::Bishop);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score += BISHOP[sq as usize] as i32;
    }

    let mut bb = board.bb(Color::White, Piece::Rook);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score += ROOK[sq as usize] as i32;
    }

    let mut bb = board.bb(Color::White, Piece::Queen);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score += QUEEN[sq as usize] as i32;
    }

    let mut bb = board.bb(Color::Black, Piece::Pawn);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score -= PAWN[mirror_vert(sq) as usize] as i32;
    }

    let mut bb = board.bb(Color::Black, Piece::Knight);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score -= KNIGHT[mirror_vert(sq) as usize] as i32;
    }

    let mut bb = board.bb(Color::Black, Piece::Bishop);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score -= BISHOP[mirror_vert(sq) as usize] as i32;
    }

    let mut bb = board.bb(Color::Black, Piece::Rook);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score -= ROOK[mirror_vert(sq) as usize] as i32;
    }

    let mut bb = board.bb(Color::Black, Piece::Queen);
    while bb != 0 {
        let sq = pop_lsb(&mut bb);
        score -= QUEEN[mirror_vert(sq) as usize] as i32;
    }

    score
}

#[cfg(not(feature = "psqt"))]
pub fn eval_psqt(_board: &Board) -> i32 {
    0
}

pub fn static_eval(board: &Board) -> i32 {
    eval_material(board) + eval_psqt(board)
}
