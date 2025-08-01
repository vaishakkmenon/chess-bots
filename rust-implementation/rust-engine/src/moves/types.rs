use crate::board::Piece;
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
