use crate::board::{Board, Color, Piece};

const P: i32 = 100;
const N: i32 = 320;
const B: i32 = 330;
const R: i32 = 500;
const Q: i32 = 900;
const TEMPO_BONUS: i32 = 10;

#[cfg(feature = "psqt")]
// Helper to mirror file
#[inline(always)]
pub const fn mirror_vert(sq: u8) -> u8 {
    sq ^ 56
}

#[cfg(feature = "psqt")]
mod psqt_tables {
    // Pawn PST - encourages center control and advancement
    // Rewards pushing pawns forward, especially in center
    pub const PAWN: [i16; 64] = [
        0, 0, 0, 0, 0, 0, 0, 0, // Rank 1
        5, 10, 10, -20, -20, 10, 10, 5, // Rank 2
        5, -5, -10, 0, 0, -10, -5, 5, // Rank 3
        0, 0, 0, 20, 20, 0, 0, 0, // Rank 4
        5, 5, 10, 25, 25, 10, 5, 5, // Rank 5
        10, 10, 20, 30, 30, 20, 10, 10, // Rank 6
        50, 50, 50, 50, 50, 50, 50, 50, // Rank 7
        0, 0, 0, 0, 0, 0, 0, 0, // Rank 8
    ];

    // Knight PST - prefers center, heavily penalizes edges
    // Knights on the rim are dim!
    pub const KNIGHT: [i16; 64] = [
        -50, -40, -30, -30, -30, -30, -40, -50, -40, -20, 0, 5, 5, 0, -20, -40, -30, 5, 10, 15, 15,
        10, 5, -30, -30, 0, 15, 20, 20, 15, 0, -30, -30, 5, 15, 20, 20, 15, 5, -30, -30, 0, 10, 15,
        15, 10, 0, -30, -40, -20, 0, 0, 0, 0, -20, -40, -50, -40, -30, -30, -30, -30, -40, -50,
    ];

    // Bishop PST - likes long diagonals and fianchetto
    // Penalizes being blocked by own pawns
    pub const BISHOP: [i16; 64] = [
        -20, -10, -10, -10, -10, -10, -10, -20, -10, 5, 0, 0, 0, 0, 5, -10, -10, 10, 10, 10, 10,
        10, 10, -10, -10, 0, 10, 10, 10, 10, 0, -10, -10, 5, 5, 10, 10, 5, 5, -10, -10, 0, 5, 10,
        10, 5, 0, -10, -10, 0, 0, 0, 0, 0, 0, -10, -20, -10, -10, -10, -10, -10, -10, -20,
    ];

    // Rook PST - loves 7th rank, prefers central files
    // Generally wants to be active
    pub const ROOK: [i16; 64] = [
        0, 0, 0, 5, 5, 0, 0, 0, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0,
        0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, 5, 10, 10, 10, 10, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0,
    ];

    // Queen PST - discourages early development
    // Penalizes moving queen out too soon (classic beginner mistake)
    pub const QUEEN: [i16; 64] = [
        -20, -10, -10, -5, -5, -10, -10, -20, -10, 0, 5, 0, 0, 0, 0, -10, -10, 5, 5, 5, 5, 5, 0,
        -10, 0, 0, 5, 5, 5, 5, 0, -5, -5, 0, 5, 5, 5, 5, 0, -5, -10, 0, 5, 5, 5, 5, 0, -10, -10, 0,
        0, 0, 0, 0, 0, -10, -20, -10, -10, -5, -5, -10, -10, -20,
    ];
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
    let material = eval_material(board);
    let psqt = eval_psqt(board);
    let mut white_score = material + (psqt / 5);

    // Give small advantage to side to move
    white_score += if board.side_to_move == Color::White {
        TEMPO_BONUS
    } else {
        -TEMPO_BONUS
    };

    if board.side_to_move == Color::White {
        white_score
    } else {
        -white_score
    }
}
