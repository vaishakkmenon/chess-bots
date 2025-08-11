use crate::board::{Color, Piece};
use crate::square::Square;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Move {
    pub from: Square,
    pub to: Square,
    pub piece: Piece,
    pub promotion: Option<Piece>,
    pub is_capture: bool,
    pub is_en_passant: bool,
    pub is_castling: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Undo {
    pub from: Square,
    pub to: Square,
    pub piece: Piece,
    pub color: Color,
    pub prev_side: Color,
    pub capture: Option<(Color, Piece, Square)>,
    pub castling_rook: Option<(Square /*rook_from*/, Square /*rook_to*/)>,

    pub prev_castling_rights: u8,
    pub promotion: Option<Piece>,
    pub prev_en_passant: Option<Square>,

    pub prev_halfmove_clock: u32,
    pub prev_fullmove_number: u32,
    // Optional if using hashing:
    // pub prev_hash: u64,
}
