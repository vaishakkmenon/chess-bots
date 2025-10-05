use crate::board::{Board, Color, Piece};

const P: i32 = 100;
const N: i32 = 320;
const B: i32 = 330;
const R: i32 = 500;
const Q: i32 = 900;

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
