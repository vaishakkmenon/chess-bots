mod fen;

use crate::bitboard::BitboardExt;
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

// Empty square value, no piece 0-11 will coincide with 255
pub(crate) const EMPTY_SQ: u8 = 0xFF;

/// Which side is to move.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Color {
    White,
    Black,
}

/// Piece enum to hold all types of pieces
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
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
    pub piece_bb: [[u64; 6]; 2],
    /// Occupancy fields
    pub occ_white: u64,
    pub occ_black: u64,
    pub occ_all: u64,
    /// Lookup table for each square
    pub piece_on_sq: [u8; 64], // new table: 0xFF = empty, 0–11 = (color<<3)|piece
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
    #[inline(always)]
    pub(crate) fn bb(&self, color: Color, piece: Piece) -> u64 {
        self.piece_bb[color as usize][piece as usize]
    }

    #[inline(always)]
    pub(crate) fn set_bb(&mut self, color: Color, piece: Piece, new_bb: u64) {
        let idx = color as usize;
        let p = piece as usize;

        // 1) Read old bitboard
        let old_bb = self.piece_bb[idx][p];

        // 2) Compute which bits changed (set or cleared)
        let delta = old_bb ^ new_bb;

        // 3) Early out if nothing changed
        if delta == 0 {
            return;
        }
        // 4) Store new bitboard
        self.piece_bb[idx][p] = new_bb;

        // 5) Update side‐occupancy by XOR’ing the delta
        if color == Color::White {
            self.occ_white ^= delta;
        } else {
            self.occ_black ^= delta;
        }

        // 6) Recompute the global occupancy
        self.occ_all = self.occ_white | self.occ_black;

        let mut bits_to_update = delta;
        while bits_to_update != 0 {
            // Isolate the least significant 1-bit
            let single_bit = bits_to_update & (!bits_to_update + 1);

            // Compute the square index (0–63) from that bit
            let square_index = single_bit.trailing_zeros() as u8;
            let square = Square::from_index(square_index);

            // If the bit is set in the new bitboard, place the piece;
            // otherwise clear the square
            if new_bb & single_bit != 0 {
                self.place_piece_at_sq(color, piece, square);
            } else {
                self.clear_square(square);
            }

            // Remove that bit from bits_to_update
            bits_to_update &= bits_to_update - 1;
        }
    }

    #[inline(always)]
    pub(crate) fn clear_square(&mut self, sq: Square) {
        let i = sq.index() as usize;
        self.piece_on_sq[i] = EMPTY_SQ;
    }

    #[inline(always)]
    pub(crate) fn place_piece_at_sq(&mut self, color: Color, piece: Piece, sq: Square) {
        let i = sq.index() as usize;
        self.piece_on_sq[i] = (color as u8) << 3 | (piece as u8);
    }

    /// Create an empty board (all bitboards zero, White to move).
    pub fn new_empty() -> Self {
        Board {
            piece_bb: [[0u64; 6]; 2],
            occ_white: 0,
            occ_black: 0,
            occ_all: 0,
            piece_on_sq: [EMPTY_SQ; 64],
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
        b.set_bb(Color::White, Piece::Pawn, WHITE_PAWN_MASK);
        b.set_bb(Color::White, Piece::Bishop, WHITE_BISHOP_MASK);
        b.set_bb(Color::White, Piece::Knight, WHITE_KNIGHT_MASK);
        b.set_bb(Color::White, Piece::Rook, WHITE_ROOK_MASK);
        b.set_bb(Color::White, Piece::Queen, WHITE_QUEEN_MASK);
        b.set_bb(Color::White, Piece::King, WHITE_KING_MASK);

        // Set up black pieces
        b.set_bb(Color::Black, Piece::Pawn, BLACK_PAWN_MASK);
        b.set_bb(Color::Black, Piece::Bishop, BLACK_BISHOP_MASK);
        b.set_bb(Color::Black, Piece::Knight, BLACK_KNIGHT_MASK);
        b.set_bb(Color::Black, Piece::Rook, BLACK_ROOK_MASK);
        b.set_bb(Color::Black, Piece::Queen, BLACK_QUEEN_MASK);
        b.set_bb(Color::Black, Piece::King, BLACK_KING_MASK);

        // Setup side to move and other important information
        b.side_to_move = Color::White;
        b.castling_rights = CASTLE_WK | CASTLE_WQ | CASTLE_BK | CASTLE_BQ;
        b.en_passant = None;
        b.halfmove_clock = 0;
        b.fullmove_number = 1;
        b
    }

    #[inline(always)]
    /// Bitboard of all pieces (both colors).
    pub fn occupied(&self) -> u64 {
        self.occ_all
    }

    #[inline(always)]
    pub fn has_castling(&self, flag: u8) -> bool {
        self.castling_rights & flag != 0
    }

    /// Validate that no square is occupied by more than one piece.
    /// Returns Ok if valid, Err describing the overlap if invalid.
    pub fn validate(&self) -> Result<(), String> {
        let bitboards = [
            ("white_pawns", self.bb(Color::White, Piece::Pawn)),
            ("white_knights", self.bb(Color::White, Piece::Knight)),
            ("white_bishops", self.bb(Color::White, Piece::Bishop)),
            ("white_rooks", self.bb(Color::White, Piece::Rook)),
            ("white_queens", self.bb(Color::White, Piece::Queen)),
            ("white_king", self.bb(Color::White, Piece::King)),
            ("black_pawns", self.bb(Color::Black, Piece::Pawn)),
            ("black_knights", self.bb(Color::Black, Piece::Knight)),
            ("black_bishops", self.bb(Color::Black, Piece::Bishop)),
            ("black_rooks", self.bb(Color::Black, Piece::Rook)),
            ("black_queens", self.bb(Color::Black, Piece::Queen)),
            ("black_king", self.bb(Color::Black, Piece::King)),
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

    #[inline(always)]
    /// Bitboard of all pieces for one side.
    pub fn occupancy(&self, color: Color) -> u64 {
        match color {
            Color::White => self.occ_white,
            Color::Black => self.occ_black,
        }
    }

    /// Shorthand for the opponent’s occupancy.
    pub fn opponent_occupancy(&self, color: Color) -> u64 {
        self.occupancy(color.opposite())
    }

    #[inline(always)]
    /// Single‐slot accessor for a given piece & color.
    pub fn pieces(&self, piece: Piece, color: Color) -> u64 {
        self.bb(color, piece)
    }

    // Utility Aliases
    #[inline(always)]
    pub fn en_passant_target(&self) -> Option<Square> {
        self.en_passant
    }

    #[inline(always)]
    pub fn has_kingside_castle(&self, color: Color) -> bool {
        match color {
            Color::White => self.castling_rights & 0b0001 != 0,
            Color::Black => self.castling_rights & 0b0100 != 0,
        }
    }

    #[inline(always)]
    pub fn has_queenside_castle(&self, color: Color) -> bool {
        match color {
            Color::White => self.castling_rights & 0b0010 != 0,
            Color::Black => self.castling_rights & 0b1000 != 0,
        }
    }

    /// Function to get exactly what square the king sits on
    #[inline(always)]
    pub fn king_square(&self, color: Color) -> Square {
        let king_bb = self.pieces(Piece::King, color);
        Square::try_from(king_bb.lsb()).expect("Invalid king bitboard")
    }
}

impl Color {
    pub fn opposite(self) -> Self {
        match self {
            Color::White => Color::Black,
            Color::Black => Color::White,
        }
    }

    /// Decode a 0/1 value into a Color.
    #[inline(always)]
    pub(crate) fn from_u8(v: u8) -> Self {
        match v {
            0 => Color::White,
            1 => Color::Black,
            _ => panic!("Invalid Color encoding: {}", v),
        }
    }
}

impl Piece {
    /// Decode a 0–5 value into a Piece.
    #[inline(always)]
    pub(crate) fn from_u8(v: u8) -> Self {
        match v {
            0 => Piece::Pawn,
            1 => Piece::Knight,
            2 => Piece::Bishop,
            3 => Piece::Rook,
            4 => Piece::Queen,
            5 => Piece::King,
            _ => panic!("Invalid Piece encoding: {}", v),
        }
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
mod tests;
