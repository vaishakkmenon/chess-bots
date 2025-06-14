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
    pub white_kings: u64,
    pub black_pawns: u64,
    pub black_knights: u64,
    pub black_bishops: u64,
    pub black_rooks: u64,
    pub black_queens: u64,
    pub black_kings: u64,
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
            white_kings: 0,
            black_pawns: 0,
            black_knights: 0,
            black_bishops: 0,
            black_rooks: 0,
            black_queens: 0,
            black_kings: 0,
            side_to_move: Color::White,
        }
    }
    pub fn occupied(&self) -> u64 {
        self.white_pawns
            | self.white_bishops
            | self.white_knights
            | self.white_rooks
            | self.white_queens
            | self.white_kings
            | self.black_pawns
            | self.black_bishops
            | self.black_knights
            | self.black_rooks
            | self.black_queens
            | self.black_kings
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
}
