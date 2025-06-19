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
}

/// An all-zero board (no pieces) with White to move.
impl Default for Board {
    fn default() -> Self {
        Board::new_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_empty_board() {
        let b = Board::new_empty();

        // All piece bitboards should be zero:
        assert_empty_board(&b);

        // Move‐clock fields:
        assert_eq!(b.halfmove_clock, 0);
        assert_eq!(b.fullmove_number, 1);

        // Side to move:
        assert!(
            matches!(b.side_to_move, Color::White),
            "Expected White to move on a new empty board"
        );

        // Castling rights & en passant:
        assert_empty_castling(&b);
        assert!(b.en_passant.is_none());
    }

    // Helper in tests:
    fn assert_empty_board(b: &Board) {
        for &bb in &[
            b.white_pawns,
            b.white_knights,
            b.white_bishops,
            b.white_rooks,
            b.white_queens,
            b.white_king,
            b.black_pawns,
            b.black_knights,
            b.black_bishops,
            b.black_rooks,
            b.black_queens,
            b.black_king,
        ] {
            assert_eq!(bb, 0);
        }
    }

    fn assert_empty_castling(b: &Board) {
        for &bb in &[CASTLE_WK, CASTLE_WQ, CASTLE_BK, CASTLE_BQ] {
            assert_eq!(b.has_castling(bb), false);
        }
    }

    #[test]
    fn test_starting_position_pawns() {
        let b = Board::new();
        assert_eq!(b.white_pawns, WHITE_PAWN_MASK);
        assert_eq!(b.black_pawns, BLACK_PAWN_MASK);
    }

    #[test]
    fn test_starting_position_white_backrank() {
        let b = Board::new();
        // Verify individual back-rank pieces
        assert_eq!(b.white_rooks, WHITE_ROOK_MASK);
        assert_eq!(b.white_knights, WHITE_KNIGHT_MASK);
        assert_eq!(b.white_bishops, WHITE_BISHOP_MASK);
        assert_eq!(b.white_queens, WHITE_QUEEN_MASK);
        assert_eq!(b.white_king, WHITE_KING_MASK);
    }

    #[test]
    fn test_starting_position_black_backrank() {
        let b = Board::new();
        // Verify individual back-rank pieces
        assert_eq!(b.black_rooks, BLACK_ROOK_MASK);
        assert_eq!(b.black_knights, BLACK_KNIGHT_MASK);
        assert_eq!(b.black_bishops, BLACK_BISHOP_MASK);
        assert_eq!(b.black_queens, BLACK_QUEEN_MASK);
        assert_eq!(b.black_king, BLACK_KING_MASK);
    }

    #[test]
    fn test_full_starting_position() {
        let b = Board::new();
        // White back-rank + pawns
        let white_expected = WHITE_PAWN_MASK
            | WHITE_ROOK_MASK
            | WHITE_KNIGHT_MASK
            | WHITE_BISHOP_MASK
            | WHITE_QUEEN_MASK
            | WHITE_KING_MASK;
        // Black back-rank + pawns
        let black_expected = BLACK_PAWN_MASK
            | BLACK_ROOK_MASK
            | BLACK_KNIGHT_MASK
            | BLACK_BISHOP_MASK
            | BLACK_QUEEN_MASK
            | BLACK_KING_MASK;

        // Check each side’s pieces
        assert_eq!(b.white_pawns, WHITE_PAWN_MASK);
        assert_eq!(b.white_rooks, WHITE_ROOK_MASK);
        assert_eq!(b.white_knights, WHITE_KNIGHT_MASK);
        assert_eq!(b.white_bishops, WHITE_BISHOP_MASK);
        assert_eq!(b.white_queens, WHITE_QUEEN_MASK);
        assert_eq!(b.white_king, WHITE_KING_MASK);

        assert_eq!(b.black_pawns, BLACK_PAWN_MASK);
        assert_eq!(b.black_rooks, BLACK_ROOK_MASK);
        assert_eq!(b.black_knights, BLACK_KNIGHT_MASK);
        assert_eq!(b.black_bishops, BLACK_BISHOP_MASK);
        assert_eq!(b.black_queens, BLACK_QUEEN_MASK);
        assert_eq!(b.black_king, BLACK_KING_MASK);

        // And ensure the overall occupied mask covers both sides
        assert_eq!(b.occupied(), white_expected | black_expected);
    }

    #[test]
    fn test_new_board_castling() {
        let b = Board::new();
        assert!(b.has_castling(CASTLE_WK));
        assert!(b.has_castling(CASTLE_WQ));
        assert!(b.has_castling(CASTLE_BK));
        assert!(b.has_castling(CASTLE_BQ));
    }

    #[test]
    fn test_new_board_defaults() {
        let b = Board::new();

        // Move‐clock fields:
        assert_eq!(b.halfmove_clock, 0, "Starting halfmove clock should be 0");
        assert_eq!(b.fullmove_number, 1, "Starting fullmove number should be 1");

        // Side to move & en passant:
        assert!(
            matches!(b.side_to_move, Color::White),
            "Expected White to move on the standard starting board"
        );
        assert!(
            b.en_passant.is_none(),
            "En passant square should be None at start"
        );

        // Occupied mask covers all pieces:
        let expected = WHITE_PAWN_MASK
            | WHITE_ROOK_MASK
            | WHITE_KNIGHT_MASK
            | WHITE_BISHOP_MASK
            | WHITE_QUEEN_MASK
            | WHITE_KING_MASK
            | BLACK_PAWN_MASK
            | BLACK_ROOK_MASK
            | BLACK_KNIGHT_MASK
            | BLACK_BISHOP_MASK
            | BLACK_QUEEN_MASK
            | BLACK_KING_MASK;
        assert_eq!(
            b.occupied(),
            expected,
            "occupied() should match all starting pieces"
        );
    }

    #[test]
    fn test_starting_placement() {
        assert_eq!(
            Board::new().placement_fen(),
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
        );
    }

    #[test]
    fn test_castling_fen() {
        let mut b = Board::new_empty();
        // no rights ⇒ "-"
        assert_eq!(b.castling_fen(), "-");

        // grant each right in isolation
        b.castling_rights = CASTLE_WK;
        assert_eq!(b.castling_fen(), "K");
        b.castling_rights = CASTLE_WQ;
        assert_eq!(b.castling_fen(), "Q");
        b.castling_rights = CASTLE_BK;
        assert_eq!(b.castling_fen(), "k");
        b.castling_rights = CASTLE_BQ;
        assert_eq!(b.castling_fen(), "q");

        // starting full rights
        b = Board::new();
        assert_eq!(b.castling_fen(), "KQkq");
    }

    #[test]
    fn test_en_passant_fen_helper() {
        let mut b = Board::new_empty();
        // default None → "-"
        assert_eq!(b.en_passant_fen(), "-");

        // set en_passant to e3
        let sq_e3 = "e3".parse::<Square>().unwrap();
        b.en_passant = Some(sq_e3);
        assert_eq!(b.en_passant_fen(), "e3");

        // set en_passant to h6
        let sq_h6 = "h6".parse::<Square>().unwrap();
        b.en_passant = Some(sq_h6);
        assert_eq!(b.en_passant_fen(), "h6");
    }

    #[test]
    fn test_to_fen_starting_position() {
        // The full FEN for a fresh new board:
        let expected = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
        assert_eq!(Board::new().to_fen(), expected);
    }

    #[test]
    fn test_to_fen_empty_board() {
        // An empty board (all 8s), White to move, no castling, no en-passant:
        let expected = "8/8/8/8/8/8/8/8 w - - 0 1";
        assert_eq!(Board::new_empty().to_fen(), expected);
    }
}
