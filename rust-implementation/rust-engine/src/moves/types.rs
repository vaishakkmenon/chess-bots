use crate::board::{Color, Piece};
use crate::square::Square;

use std::fmt;

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

impl fmt::Display for Move {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // Start with from->to like e2e4
        let mut s = format!("{}{}", self.from, self.to);

        // Add promotion piece if applicable (lowercase for UCI style)
        if let Some(promo) = self.promotion {
            let c = match promo {
                Piece::Queen => 'q',
                Piece::Rook => 'r',
                Piece::Bishop => 'b',
                Piece::Knight => 'n',
                _ => '?', // Should never happen
            };
            s.push(c);
        }

        // If verbose mode requested, we could add special tags
        if f.alternate() {
            // like "{:#}" formatting
            if self.is_castling {
                s.push_str(" (castle)");
            } else if self.is_en_passant {
                s.push_str(" (ep)");
            } else if self.is_capture {
                s.push_str(" (x)");
            }
        }

        write!(f, "{}", s)
    }
}
