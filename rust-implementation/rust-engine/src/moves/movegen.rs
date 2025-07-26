use crate::board::{Board, Piece};
use crate::moves::knight::KNIGHT_ATTACKS;
use crate::moves::magic::masks::bishop_vision_mask;
use crate::moves::magic::structs::BishopMagicTables;
use crate::moves::types::Move;
use crate::square::Square;

pub fn generate_knight_moves(board: &Board, moves: &mut Vec<Move>) {
    let color = board.side_to_move;
    let knights = board.pieces(Piece::Knight, color);
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);

    let mut bb = knights;
    while bb != 0 {
        let from = bb.trailing_zeros() as u8;
        bb &= bb - 1;

        let targets = KNIGHT_ATTACKS[from as usize] & !friendly;

        let mut targets_bb = targets;
        while targets_bb != 0 {
            let to = targets_bb.trailing_zeros() as u8;
            targets_bb &= targets_bb - 1;

            moves.push(Move {
                from: Square::from_index(from),
                to: Square::from_index(to),
                promotion: None,
                is_capture: (1u64 << to) & enemy != 0,
                is_en_passant: false,
                is_castling: false,
            });
        }
    }
}

pub fn generate_bishop_moves(board: &Board, tables: &BishopMagicTables, moves: &mut Vec<Move>) {
    let color = board.side_to_move;
    let bishops = board.pieces(Piece::Bishop, color);
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);
    let blockers = board.occupied();

    let mut bb = bishops;
    while bb != 0 {
        let from = bb.trailing_zeros() as u8;
        bb &= bb - 1;

        let mask = bishop_vision_mask(from as usize);
        let attacks = tables.get_attacks(from as usize, blockers, mask);

        let targets = attacks & !friendly;
        let mut targets_bb = targets;
        while targets_bb != 0 {
            let to = targets_bb.trailing_zeros() as u8;
            targets_bb &= targets_bb - 1;

            moves.push(Move {
                from: Square::from_index(from),
                to: Square::from_index(to),
                promotion: None,
                is_capture: (1u64 << to) & enemy != 0,
                is_en_passant: false,
                is_castling: false,
            });
        }
    }
}
