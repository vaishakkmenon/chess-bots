use crate::board::{Board, Color, Piece};
use crate::moves::king::KING_ATTACKS;
use crate::moves::knight::KNIGHT_ATTACKS;
use crate::moves::magic::MagicTables;
use crate::moves::magic::loader::load_magic_tables;
use crate::moves::magic::masks::{bishop_vision_mask, rook_vision_mask};
use crate::moves::pawn::pawn_attacks;
use crate::square::Square;

/// Returns a bitboard showing all the squares that *piece* could attack from *square*
pub fn attacks_from(
    piece: Piece,
    color: Color,
    square: u8,
    blockers: u64,
    tables: &MagicTables,
) -> u64 {
    let sq = square as usize;

    match piece {
        Piece::Knight => KNIGHT_ATTACKS[sq],
        Piece::King => KING_ATTACKS[sq],
        Piece::Pawn => pawn_attacks(square, color),
        Piece::Bishop => {
            let mask = bishop_vision_mask(square as usize);
            tables.bishop.get_attacks(square as usize, blockers, mask)
        }
        Piece::Rook => {
            let mask = rook_vision_mask(sq);
            tables.rook.get_attacks(sq, blockers, mask)
        }
        Piece::Queen => {
            let mask_b = bishop_vision_mask(sq);
            let mask_r = rook_vision_mask(sq);
            let b = tables.bishop.get_attacks(sq, blockers, mask_b);
            let r = tables.rook.get_attacks(sq, blockers, mask_r);
            b | r
        }
    }
}

fn is_square_attacked(
    board: &Board,
    square: Square,
    attacker: Color,
    tables: &MagicTables,
) -> bool {
    let index = square.index();
    if pawn_attacks(index, attacker) & board.pieces(Piece::Pawn, attacker) != 0 {
        return true;
    }
    if KNIGHT_ATTACKS[index as usize] & board.pieces(Piece::Knight, attacker) != 0 {
        return true;
    }
    if KING_ATTACKS[index as usize] & board.pieces(Piece::King, attacker) != 0 {
        return true;
    }

    let occupied = board.occupied();

    let rook_mask = rook_vision_mask(index as usize);
    let rook_attacks = tables.rook.get_attacks(index as usize, occupied, rook_mask);
    if rook_attacks & board.pieces(Piece::Rook, attacker) != 0 {
        return true;
    }

    let bishop_mask = bishop_vision_mask(index as usize);
    let bishop_attacks = tables
        .bishop
        .get_attacks(index as usize, occupied, bishop_mask);
    if bishop_attacks & board.pieces(Piece::Bishop, attacker) != 0 {
        return true;
    }

    let queen_attacks = tables.queen_attacks(index as usize, occupied);
    if queen_attacks & board.pieces(Piece::Queen, attacker) != 0 {
        return true;
    }

    false
}

// pub fn in_check(board: &Board, color: Color) -> bool {
//     let king_bb = if color == Color::White {
//         board.white_king
//     } else {
//         board.black_king
//     };

//     let king_sq: u8 = king_bb.trailing_zeros() as u8;

//     true
// }

/// Test suite for the `attacks_from` function across all piece types
#[cfg(test)]
mod tests {
    use super::*;
    use crate::board::{Color, Piece};
    use crate::moves::magic::{MagicTableSeed, generate_magic_tables};
    use crate::moves::magic::{bishop_vision_mask, rook_vision_mask};
    use crate::moves::{king, knight, pawn};

    fn tables() -> MagicTables {
        generate_magic_tables(MagicTableSeed::Fixed(42)).unwrap()
    }

    #[test]
    fn knight_attacks_center() {
        let t = tables();
        let d4 = 3 + 8 * 3;
        assert_eq!(
            attacks_from(Piece::Knight, Color::White, d4, 0, &t),
            knight::KNIGHT_ATTACKS[d4 as usize]
        );
    }

    #[test]
    fn knight_attacks_corner() {
        let t = tables();
        let a1 = 0;
        assert_eq!(
            attacks_from(Piece::Knight, Color::Black, a1, 0, &t),
            knight::KNIGHT_ATTACKS[a1 as usize]
        );
    }

    #[test]
    fn king_attacks_center() {
        let t = tables();
        let d4 = 3 + 8 * 3;
        assert_eq!(
            attacks_from(Piece::King, Color::White, d4, 0, &t),
            king::KING_ATTACKS[d4 as usize]
        );
    }

    #[test]
    fn king_attacks_corner() {
        let t = tables();
        let h8 = 7 + 8 * 7;
        assert_eq!(
            attacks_from(Piece::King, Color::White, h8, 0, &t),
            king::KING_ATTACKS[h8 as usize]
        );
    }

    #[test]
    fn white_pawn_attacks_center() {
        let t = tables();
        let e4 = 4 + 8 * 3;
        assert_eq!(
            attacks_from(Piece::Pawn, Color::White, e4, 0, &t),
            pawn::pawn_attacks(e4, Color::White)
        );
    }

    #[test]
    fn black_pawn_attacks_edge() {
        let t = tables();
        let a5 = 8 * 4;
        assert_eq!(
            attacks_from(Piece::Pawn, Color::Black, a5, 0, &t),
            pawn::pawn_attacks(a5, Color::Black)
        );
    }

    #[test]
    fn bishop_attacks_empty_board() {
        let t = tables();
        let c1 = 2;
        let blockers = 0;
        let mask = bishop_vision_mask(c1);
        let expected = t.bishop.get_attacks(c1, blockers, mask);
        assert_eq!(
            attacks_from(Piece::Bishop, Color::White, c1 as u8, blockers, &t),
            expected
        );
    }

    #[test]
    fn bishop_attacks_with_blockers() {
        let t = tables();
        let d4 = 3 + 8 * 3;
        let blockers = (1 << (d4 + 9)) | (1 << (d4 - 9));
        let mask = bishop_vision_mask(d4);
        let expected = t.bishop.get_attacks(d4, blockers, mask);
        assert_eq!(
            attacks_from(Piece::Bishop, Color::White, d4 as u8, blockers, &t),
            expected
        );
    }

    #[test]
    fn rook_attacks_empty_board() {
        let t = tables();
        let a1 = 0;
        let blockers = 0;
        let mask = rook_vision_mask(a1);
        let expected = t.rook.get_attacks(a1, blockers, mask);
        assert_eq!(
            attacks_from(Piece::Rook, Color::Black, a1 as u8, blockers, &t),
            expected
        );
    }

    #[test]
    fn rook_attacks_with_blockers() {
        let t = tables();
        let e5 = 4 + 8 * 4;
        let blockers = (1 << (e5 + 8)) | (1 << (e5 - 1));
        let mask = rook_vision_mask(e5);
        let expected = t.rook.get_attacks(e5, blockers, mask);
        assert_eq!(
            attacks_from(Piece::Rook, Color::Black, e5 as u8, blockers, &t),
            expected
        );
    }

    #[test]
    fn queen_attacks_combined() {
        let t = tables();
        let e4 = 4 + 8 * 3;
        let blockers = (1 << (e4 + 8)) | (1 << (e4 - 7));
        let b_mask = bishop_vision_mask(e4);
        let r_mask = rook_vision_mask(e4);
        let expected =
            t.bishop.get_attacks(e4, blockers, b_mask) | t.rook.get_attacks(e4, blockers, r_mask);
        assert_eq!(
            attacks_from(Piece::Queen, Color::White, e4 as u8, blockers, &t),
            expected
        );
    }
}
