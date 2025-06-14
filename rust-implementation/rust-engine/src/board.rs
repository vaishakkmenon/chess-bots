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

/// Which side is to move.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Color {
    White,
    Black,
}

/// Core board representation using bitboards.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Board {
    pub white_pawns: u64,
    pub white_knights: u64,
    pub white_bishops: u64,
    pub white_rooks: u64,
    pub white_queens: u64,
    pub white_king: u64,
    pub black_pawns: u64,
    pub black_knights: u64,
    pub black_bishops: u64,
    pub black_rooks: u64,
    pub black_queens: u64,
    pub black_king: u64,
    pub side_to_move: Color,
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
        }
    }
    pub fn new() -> Self {
        let mut b = Board::new_empty();
        b.white_pawns = WHITE_PAWN_MASK;
        b.white_bishops = WHITE_BISHOP_MASK;
        b.white_knights = WHITE_KNIGHT_MASK;
        b.white_rooks = WHITE_ROOK_MASK;
        b.white_queens = WHITE_QUEEN_MASK;
        b.white_king = WHITE_KING_MASK;

        b.black_pawns = BLACK_PAWN_MASK;
        b.black_rooks = BLACK_ROOK_MASK;
        b.black_knights = BLACK_KNIGHT_MASK;
        b.black_bishops = BLACK_BISHOP_MASK;
        b.black_queens = BLACK_QUEEN_MASK;
        b.black_king = BLACK_KING_MASK;
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
        assert_eq!(b.white_pawns, 0);
        assert_eq!(b.black_pawns, 0);
        match b.side_to_move {
            Color::White => (),
            Color::Black => panic!("Expected White to move on a new empty board"),
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
}
