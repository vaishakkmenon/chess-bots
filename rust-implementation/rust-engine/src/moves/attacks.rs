use crate::board::{Color, Piece};
use crate::moves::{king, knight, pawn};

/// Returns a bitboard showing all the squares that *piece* could attack from *square*
pub fn attacks_from(piece: Piece, color: Color, square: u8) -> u64 {
    match piece {
        Piece::Knight => knight::KNIGHT_ATTACKS[square as usize],
        Piece::King => king::KING_ATTACKS[square as usize],
        Piece::Pawn => pawn::pawn_attacks(square, color),
        // Placeholder for sliding pieces
        _ => 0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::{Color, Piece};

    #[test]
    fn test_attacks_from_knight_d4() {
        let d4 = 3 + 8 * 3; // d4 = index 27
        let expected = knight::KNIGHT_ATTACKS[d4];
        assert_eq!(
            attacks_from(Piece::Knight, Color::White, d4 as u8),
            expected
        );
    }

    #[test]
    fn test_attacks_from_white_pawn_d4() {
        let d4: u8 = 3 + 8 * 3; // d4 = index 27
        let expected = pawn::pawn_attacks(d4, Color::White);
        assert_eq!(attacks_from(Piece::Pawn, Color::White, d4), expected);
    }

    #[test]
    fn test_attacks_from_knight_b1() {
        let b1: u8 = 1;
        let expected = knight::KNIGHT_ATTACKS[b1 as usize];
        assert_eq!(attacks_from(Piece::Knight, Color::White, b1), expected);
    }

    #[test]
    fn test_attacks_from_king_e1() {
        let e1: u8 = 4;
        let expected = king::KING_ATTACKS[e1 as usize];
        assert_eq!(attacks_from(Piece::King, Color::Black, e1), expected);
    }

    #[test]
    fn test_attacks_from_white_pawn_edge() {
        let h4: u8 = 7 + 8 * 3; // h4 (square index 31)
        let expected = pawn::pawn_attacks(h4, Color::White);
        assert_eq!(attacks_from(Piece::Pawn, Color::White, h4), expected);
    }

    #[test]
    fn test_attacks_from_black_pawn_center() {
        let e5: u8 = 4 + 8 * 4; // e5 (square index 36)
        let expected = pawn::pawn_attacks(e5, Color::Black);
        assert_eq!(attacks_from(Piece::Pawn, Color::Black, e5), expected);
    }
}
