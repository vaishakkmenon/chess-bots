use crate::square::Square;

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

    /// Generate the piece‐placement portion of FEN (e.g., "rnbqkbnr/pppppppp/8/...").
    fn placement_fen(&self) -> String {
        let mut fen = String::new();

        // Loop ranks 8 down to 1 (rank_idx 7 → 0)
        for rank in (0..8).rev() {
            let mut empty = 0;

            // Loop files a through h (file_idx 0 → 7)
            for file in 0..8 {
                let idx = rank * 8 + file;
                let bit = 1u64 << idx;

                // Determine which piece (if any) occupies this square:
                let piece_char = if self.white_pawns & bit != 0 {
                    Some('P')
                } else if self.white_knights & bit != 0 {
                    Some('N')
                } else if self.white_bishops & bit != 0 {
                    Some('B')
                } else if self.white_rooks & bit != 0 {
                    Some('R')
                } else if self.white_queens & bit != 0 {
                    Some('Q')
                } else if self.white_king & bit != 0 {
                    Some('K')
                } else if self.black_pawns & bit != 0 {
                    Some('p')
                } else if self.black_knights & bit != 0 {
                    Some('n')
                } else if self.black_bishops & bit != 0 {
                    Some('b')
                } else if self.black_rooks & bit != 0 {
                    Some('r')
                } else if self.black_queens & bit != 0 {
                    Some('q')
                } else if self.black_king & bit != 0 {
                    Some('k')
                } else {
                    None
                };

                if let Some(ch) = piece_char {
                    // Flush any accumulated empties
                    if empty > 0 {
                        fen.push_str(&empty.to_string());
                        empty = 0;
                    }
                    fen.push(ch);
                } else {
                    // Empty square
                    empty += 1;
                }
            }

            // After finishing the rank, flush trailing empties
            if empty > 0 {
                fen.push_str(&empty.to_string());
            }

            // Add '/' between ranks (but not after the last one)
            if rank > 0 {
                fen.push('/');
            }
        }
        return fen;
    }

    pub fn castling_fen(&self) -> String {
        let mut s = String::new();

        if self.has_castling(CASTLE_WK) {
            s.push('K');
        }
        if self.has_castling(CASTLE_WQ) {
            s.push('Q');
        }
        if self.has_castling(CASTLE_BK) {
            s.push('k');
        }
        if self.has_castling(CASTLE_BQ) {
            s.push('q');
        }

        if s.is_empty() {
            s.push('-');
        }

        return s;
    }

    pub fn en_passant_fen(&self) -> String {
        match self.en_passant {
            Some(sq) => sq.to_string(),
            None => "-".to_string(),
        }
    }

    pub fn to_fen(&self) -> String {
        format!(
            "{} {} {} {} {} {}",
            self.placement_fen(),
            if self.side_to_move == Color::White {
                'w'
            } else {
                'b'
            },
            self.castling_fen(),
            self.en_passant_fen(),
            self.halfmove_clock,
            self.fullmove_number,
        )
    }

    /// Split into six fields, validate count
    fn split_fen(fen: &str) -> Result<(&str, &str, &str, &str, &str, &str), String> {
        let p: Vec<&str> = fen.split_whitespace().collect();
        if p.len() != 6 {
            return Err(format!("Expected 6 FEN fields, found {}", p.len()));
        }
        Ok((p[0], p[1], p[2], p[3], p[4], p[5]))
    }

    fn parse_placement(&mut self, placement: &str) -> Result<(), String> {
        *self = Board::new_empty(); // reset the board
        let ranks: Vec<&str> = placement.split('/').collect();
        if ranks.len() != 8 {
            return Err(format!("Expected 8 ranks, got {}", ranks.len()));
        }
        for (i, &rank_str) in ranks.iter().enumerate() {
            let rank = 7 - i;
            self.parse_rank(rank, rank_str)?; // call the method on `self`
        }
        Ok(())
    }

    fn parse_rank(&mut self, rank: usize, rank_str: &str) -> Result<(), String> {
        let mut file = 0u8;
        for ch in rank_str.chars() {
            if file >= 8 {
                return Err(format!(
                    "Too many squares on rank {}: {}",
                    8 - rank,
                    rank_str
                ));
            }
            if let Some(skip) = ch.to_digit(10) {
                // Digit: skip that many empty files
                file = file
                    .checked_add(skip as u8)
                    .ok_or_else(|| format!("Invalid skip {} on rank {}", skip, rank))?;
            } else {
                // Letter: set a piece at (rank, file)
                let idx = rank * 8 + file as usize;
                self.set_piece_at(ch, idx)?;
                file += 1;
            }
        }
        if file != 8 {
            return Err(format!(
                "Not enough squares on rank {}: {}",
                8 - rank,
                rank_str
            ));
        }
        Ok(())
    }

    fn set_piece_at(&mut self, ch: char, idx: usize) -> Result<(), String> {
        let mask = 1u64 << idx;
        match ch {
            'P' => self.white_pawns |= mask,
            'N' => self.white_knights |= mask,
            'B' => self.white_bishops |= mask,
            'R' => self.white_rooks |= mask,
            'Q' => self.white_queens |= mask,
            'K' => self.white_king |= mask,
            'p' => self.black_pawns |= mask,
            'n' => self.black_knights |= mask,
            'b' => self.black_bishops |= mask,
            'r' => self.black_rooks |= mask,
            'q' => self.black_queens |= mask,
            'k' => self.black_king |= mask,
            _ => return Err(format!("Invalid piece char '{}'", ch)),
        }
        Ok(())
    }

    fn parse_active_color(&mut self, field: &str) -> Result<(), String> {
        self.side_to_move = match field {
            "w" => Color::White,
            "b" => Color::Black,
            _ => return Err(format!("Invalid active-color in FEN: `{}`", field)),
        };
        Ok(())
    }

    /// Parse the castling-rights field (e.g. "KQkq" or "-") and update `self.castling_rights`.
    fn parse_castling_rights(&mut self, field: &str) -> Result<(), String> {
        self.castling_rights = 0;

        if field == "-" {
            return Ok(());
        }

        for c in field.chars() {
            match c {
                'K' => self.castling_rights |= CASTLE_WK,
                'Q' => self.castling_rights |= CASTLE_WQ,
                'k' => self.castling_rights |= CASTLE_BK,
                'q' => self.castling_rights |= CASTLE_BQ,
                _ => {
                    return Err(format!("Invalid castling-rights character `{}`", c));
                }
            }
        }
        return Ok(());
    }

    /// Parse the en_passant field, is it a valid square or empty
    fn parse_en_passant(&mut self, field: &str) -> Result<(), String> {
        self.en_passant = if field == "-" {
            None
        } else {
            let sq = field
                .parse::<Square>()
                .map_err(|e| format!("Invalid en-passant square `{}`: {}", field, e))?;
            Some(sq)
        };
        Ok(())
    }

    /// Parse the halfmove and fullmove clock fields.
    fn parse_clocks(&mut self, halfmove_s: &str, fullmove_s: &str) -> Result<(), String> {
        self.halfmove_clock = halfmove_s
            .parse()
            .map_err(|_| format!("Invalid halfmove clock `{}`", halfmove_s))?;
        self.fullmove_number = fullmove_s
            .parse()
            .map_err(|_| format!("Invalid fullmove number `{}`", fullmove_s))?;
        Ok(())
    }

    /// Parse a FEN string and update this board’s state.
    pub fn set_fen(&mut self, fen: &str) -> Result<(), String> {
        // 1. Split into six FEN fields
        let (placement, active, castling, ep, hm, fm) = Self::split_fen(fen)?;

        // 2. Parse each field in turn
        self.parse_placement(placement)?;
        self.parse_active_color(active)?;
        self.parse_castling_rights(castling)?;
        self.parse_en_passant(ep)?;
        self.parse_clocks(hm, fm)?;

        Ok(())
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

#[cfg(test)]
#[path = "board_tests.rs"]
mod tests;
