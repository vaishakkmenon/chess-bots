mod fen;

use crate::square::Square;
use std::fmt;
use std::str::FromStr;

/// Starting position constants
// ———————— White side (ranks 1 & 2) ————————
// Pawns on rank 2: bits 8–15
const WHITE_PAWN_MASK: u64 = 0x0000_0000_0000_FF00;
// Individual back-rank pieces on rank 1:
// Rooks on a1 (bit 0) and h1 (bit 7)
const WHITE_ROOK_MASK: u64 = (1 << 0) | (1 << 7); // 0x0000_0000_0000_0081
// Knights on b1 (bit 1) and g1 (bit 6)
const WHITE_KNIGHT_MASK: u64 = (1 << 1) | (1 << 6); // 0x0000_0000_0000_0042
// Bishops on c1 (bit 2) and f1 (bit 5)
const WHITE_BISHOP_MASK: u64 = (1 << 2) | (1 << 5); // 0x0000_0000_0000_0024
// Queen on d1 (bit 3)
const WHITE_QUEEN_MASK: u64 = 1 << 3; // 0x0000_0000_0000_0008
// King on e1 (bit 4)
const WHITE_KING_MASK: u64 = 1 << 4; // 0x0000_0000_0000_0010

// ———————— Black side (ranks 7 & 8) ————————
// Pawns on rank 7: bits 48–55
const BLACK_PAWN_MASK: u64 = 0x00FF_0000_0000_0000; // a7–h7
// Individual back-rank pieces on rank 8:
// Rooks on a8 (bit 56) and h8 (bit 63)
const BLACK_ROOK_MASK: u64 = (1 << 56) | (1 << 63); // 0x8100_0000_0000_0000
// Knights on b8 (bit 57) and g8 (bit 62)
const BLACK_KNIGHT_MASK: u64 = (1 << 57) | (1 << 62); // 0x4200_0000_0000_0000
// Bishops on c8 (bit 58) and f8 (bit 61)
const BLACK_BISHOP_MASK: u64 = (1 << 58) | (1 << 61); // 0x2400_0000_0000_0000
// Queen on d8 (bit 59)
const BLACK_QUEEN_MASK: u64 = 1 << 59; // 0x0800_0000_0000_0000
// King on e8 (bit 60)
const BLACK_KING_MASK: u64 = 1 << 60; // 0x1000_0000_0000_0000

// Castling White Kingside
const CASTLE_WK: u8 = 0b0001;
// Castling White Queenside
const CASTLE_WQ: u8 = 0b0010;
// Castling Black Kingside
const CASTLE_BK: u8 = 0b0100;
// Castling Black Queenside
const CASTLE_BQ: u8 = 0b1000;

/// Which side is to move.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Color {
    White,
    Black,
}

/// Piece enum to hold all types of pieces
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Piece {
    Pawn,
    Knight,
    Bishop,
    Rook,
    Queen,
    King,
}

/// Core board representation using bitboards.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Board {
    /// White Pieces
    pub white_pawns: u64,
    pub white_knights: u64,
    pub white_bishops: u64,
    pub white_rooks: u64,
    pub white_queens: u64,
    pub white_king: u64,
    pub black_pawns: u64,
    /// Black Pieces
    pub black_knights: u64,
    pub black_bishops: u64,
    pub black_rooks: u64,
    pub black_queens: u64,
    pub black_king: u64,
    /// White or Black to move
    pub side_to_move: Color,
    /// Castling rights: bit 0=White kingside, 1=White queenside, 2=Black kingside, 3=Black queenside
    pub castling_rights: u8,
    /// En passant target square, as 0–63, or None if not available.
    pub en_passant: Option<Square>,
    /// Halfmove clock (for fifty-move draw rule).
    pub halfmove_clock: u32,
    /// Fullmove number (starts at 1 and increments after Black’s move).
    pub fullmove_number: u32,
}

impl Board {
    /// Create an empty board (all bitboards zero, White to move).
    pub fn new_empty() -> Self {
        Board {
            white_pawns: 0,
            white_knights: 0,
            white_bishops: 0,
            white_rooks: 0,
            white_queens: 0,
            white_king: 0,
            black_pawns: 0,
            black_knights: 0,
            black_bishops: 0,
            black_rooks: 0,
            black_queens: 0,
            black_king: 0,
            side_to_move: Color::White,
            castling_rights: 0,
            en_passant: None,
            halfmove_clock: 0,
            fullmove_number: 1,
        }
    }
    pub fn new() -> Self {
        let mut b = Board::new_empty();
        // Set up white pieces
        b.white_pawns = WHITE_PAWN_MASK;
        b.white_bishops = WHITE_BISHOP_MASK;
        b.white_knights = WHITE_KNIGHT_MASK;
        b.white_rooks = WHITE_ROOK_MASK;
        b.white_queens = WHITE_QUEEN_MASK;
        b.white_king = WHITE_KING_MASK;

        // Set up black pieces
        b.black_pawns = BLACK_PAWN_MASK;
        b.black_rooks = BLACK_ROOK_MASK;
        b.black_knights = BLACK_KNIGHT_MASK;
        b.black_bishops = BLACK_BISHOP_MASK;
        b.black_queens = BLACK_QUEEN_MASK;
        b.black_king = BLACK_KING_MASK;

        // Setup side to move and other important information
        b.side_to_move = Color::White;
        b.castling_rights = CASTLE_WK | CASTLE_WQ | CASTLE_BK | CASTLE_BQ;
        b.en_passant = None;
        b.halfmove_clock = 0;
        b.fullmove_number = 1;
        return b;
    }
    pub fn occupied(&self) -> u64 {
        self.white_pawns
            | self.white_bishops
            | self.white_knights
            | self.white_rooks
            | self.white_queens
            | self.white_king
            | self.black_pawns
            | self.black_bishops
            | self.black_knights
            | self.black_rooks
            | self.black_queens
            | self.black_king
    }
    pub fn has_castling(&self, flag: u8) -> bool {
        self.castling_rights & flag != 0
    }

    /// Validate that no square is occupied by more than one piece.
    /// Returns Ok if valid, Err describing the overlap if invalid.
    pub fn validate(&self) -> Result<(), String> {
        let bitboards = [
            ("white_pawns", self.white_pawns),
            ("white_knights", self.white_knights),
            ("white_bishops", self.white_bishops),
            ("white_rooks", self.white_rooks),
            ("white_queens", self.white_queens),
            ("white_king", self.white_king),
            ("black_pawns", self.black_pawns),
            ("black_knights", self.black_knights),
            ("black_bishops", self.black_bishops),
            ("black_rooks", self.black_rooks),
            ("black_queens", self.black_queens),
            ("black_king", self.black_king),
        ];

        let mut seen: u64 = 0;
        for (name, bb) in &bitboards {
            if (seen & bb) != 0 {
                return Err(format!("Bitboard `{}` overlaps with another piece", name));
            }
            seen |= bb;
        }
        Ok(())
    }
}

/// An all-zero board (no pieces) with White to move.
impl Default for Board {
    fn default() -> Self {
        Board::new_empty()
    }
}

impl FromStr for Board {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let mut board = Board::new_empty();
        board.set_fen(s)?;
        Ok(board)
    }
}

impl fmt::Display for Board {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let fen = self.to_fen();
        write!(f, "{}", fen)
    }
}

#[cfg(test)]
// #[path = "board_tests.rs"]
mod tests;
