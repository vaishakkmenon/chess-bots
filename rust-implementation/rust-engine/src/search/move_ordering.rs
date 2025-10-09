use crate::board::{Board, Piece};
use crate::moves::types::Move;
use crate::search::context::SearchContext;

/// Piece values for MVV-LVA scoring
pub const PIECE_VALUES: [i32; 6] = [
    100,   // Pawn
    320,   // Knight
    330,   // Bishop
    500,   // Rook
    900,   // Queen
    20000, // King
];

/// Get the value of a piece type
#[inline]
pub fn piece_value(piece: Piece) -> i32 {
    PIECE_VALUES[piece as usize]
}

/// Score a capture move using MVV-LVA
/// Returns: (victim_value * 10) - attacker_value + promotion_bonus
/// Higher scores = better captures (should be searched first)
pub fn mvv_lva_score(mv: &Move, board: &Board) -> i32 {
    if !mv.is_capture() {
        return 0;
    }

    let victim_value = if mv.flags & 0b0101 == 0b0101 {
        // En passant capture (flag check may differ based on your Move struct)
        piece_value(Piece::Pawn)
    } else {
        // Regular capture - get piece at destination square
        let victim_piece = Piece::from_u8(board.piece_on_sq[mv.to.index() as usize] & 0b111);
        piece_value(victim_piece)
    };

    let attacker_value = piece_value(mv.piece);

    let promo_bonus = if mv.promotion.is_some() { 800 } else { 0 };

    victim_value * 10 - attacker_value + promo_bonus
}

/// Score any move for ordering purposes
/// Returns higher scores for moves that should be searched first
pub fn score_move(mv: &Move, board: &Board, ctx: &SearchContext, ply: usize) -> i32 {
    // 1. Captures get highest priority (10000+)
    if mv.is_capture() {
        return 10000 + mvv_lva_score(mv, board);
    }

    // 2. Killer moves get priority (9000)
    if ctx.is_killer(ply, mv) {
        return 9000;
    }

    0
}

#[cfg(test)]
mod tests {
    use super::super::context::SearchContext;
    use super::*;
    use crate::board::{Board, Piece};
    use crate::square::Square;
    use std::str::FromStr;

    #[test]
    fn test_piece_values() {
        assert_eq!(piece_value(Piece::Pawn), 100);
        assert_eq!(piece_value(Piece::Knight), 320);
        assert_eq!(piece_value(Piece::Bishop), 330);
        assert_eq!(piece_value(Piece::Rook), 500);
        assert_eq!(piece_value(Piece::Queen), 900);
        assert_eq!(piece_value(Piece::King), 20000);
    }

    #[test]
    fn test_mvv_lva_pawn_takes_queen() {
        // Position: white pawn on e4, black queen on d5
        // FEN: 8/8/8/3q4/4P3/8/8/8 w - - 0 1
        let board = Board::from_str("8/8/8/3q4/4P3/8/8/8 w - - 0 1").unwrap();

        // Create move: e4xd5
        let mv = Move {
            piece: Piece::Pawn,
            from: Square::from_str("e4").unwrap(),
            to: Square::from_str("d5").unwrap(),
            promotion: None,
            flags: 0b0100, // Capture flag (may differ in your implementation)
        };

        let score = mvv_lva_score(&mv, &board);

        // Expected: (900 * 10) - 100 = 8900
        assert_eq!(score, 8900, "Pawn takes queen should score 8900");
    }

    #[test]
    fn test_mvv_lva_queen_takes_pawn() {
        // Position: white queen on d1, black pawn on d5
        // FEN: 8/8/8/3p4/8/8/8/3Q4 w - - 0 1
        let board = Board::from_str("8/8/8/3p4/8/8/8/3Q4 w - - 0 1").unwrap();

        let mv = Move {
            piece: Piece::Queen,
            from: Square::from_str("d1").unwrap(),
            to: Square::from_str("d5").unwrap(),
            promotion: None,
            flags: 0b0100, // Capture
        };

        let score = mvv_lva_score(&mv, &board);

        // Expected: (100 * 10) - 900 = 100
        assert_eq!(score, 100, "Queen takes pawn should score 100");
    }

    #[test]
    fn test_mvv_lva_queen_takes_queen() {
        // Position: white queen on d1, black queen on d5
        // FEN: 8/8/8/3q4/8/8/8/3Q4 w - - 0 1
        let board = Board::from_str("8/8/8/3q4/8/8/8/3Q4 w - - 0 1").unwrap();

        let mv = Move {
            piece: Piece::Queen,
            from: Square::from_str("d1").unwrap(),
            to: Square::from_str("d5").unwrap(),
            promotion: None,
            flags: 0b0100,
        };

        let score = mvv_lva_score(&mv, &board);

        // Expected: (900 * 10) - 900 = 8100
        assert_eq!(score, 8100, "Queen takes queen should score 8100");
    }

    #[test]
    fn test_quiet_moves_score_zero() {
        let board =
            Board::from_str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap();

        let ctx = SearchContext::new();
        let ply = 0;

        // Quiet move: e2-e4
        let mv = Move {
            piece: Piece::Pawn,
            from: Square::from_str("e2").unwrap(),
            to: Square::from_str("e4").unwrap(),
            promotion: None,
            flags: 0b0000, // No capture
        };

        let score = score_move(&mv, &board, &ctx, ply);

        assert_eq!(score, 0, "Quiet moves should score 0 in Phase 1");
    }

    #[test]
    fn test_captures_score_higher_than_quiets() {
        let board = Board::from_str("8/8/8/3p4/4P3/8/8/8 w - - 0 1").unwrap();

        let ctx = SearchContext::new();
        let ply = 0;

        // Capture: e4xd5
        let capture = Move {
            piece: Piece::Pawn,
            from: Square::from_str("e4").unwrap(),
            to: Square::from_str("d5").unwrap(),
            promotion: None,
            flags: 0b0100,
        };

        // Quiet: e4-e5 (hypothetical)
        let quiet = Move {
            piece: Piece::Pawn,
            from: Square::from_str("e4").unwrap(),
            to: Square::from_str("e5").unwrap(),
            promotion: None,
            flags: 0b0000,
        };

        let capture_score = score_move(&capture, &board, &ctx, ply);
        let quiet_score = score_move(&quiet, &board, &ctx, ply);

        assert!(
            capture_score > quiet_score,
            "Captures should score higher than quiets"
        );
        assert!(
            capture_score >= 10000,
            "Captures should score at least 10000"
        );
    }

    #[test]
    fn test_better_captures_score_higher() {
        let board = Board::from_str("8/8/8/2nq4/3N4/8/8/8 w - - 0 1").unwrap();

        let ctx = SearchContext::new();
        let ply = 0;

        // Good capture: Nxd5 (knight takes queen)
        let good_capture = Move {
            piece: Piece::Knight,
            from: Square::from_str("d4").unwrap(),
            to: Square::from_str("d5").unwrap(),
            promotion: None,
            flags: 0b0100,
        };

        // Bad capture: Nxc5 (knight takes knight)
        let bad_capture = Move {
            piece: Piece::Knight,
            from: Square::from_str("d4").unwrap(),
            to: Square::from_str("c5").unwrap(),
            promotion: None,
            flags: 0b0100,
        };

        let good_score = score_move(&good_capture, &board, &ctx, ply);
        let bad_score = score_move(&bad_capture, &board, &ctx, ply);

        assert!(good_score > bad_score, "NxQ should score higher than NxN");
    }
}
