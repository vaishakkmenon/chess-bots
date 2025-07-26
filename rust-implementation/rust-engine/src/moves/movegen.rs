use crate::board::{Board, Piece};
use crate::moves::king::KING_ATTACKS;
use crate::moves::knight::KNIGHT_ATTACKS;
use crate::moves::magic::MagicTables;
use crate::moves::magic::masks::{bishop_vision_mask, rook_vision_mask};
use crate::moves::magic::structs::{BishopMagicTables, RookMagicTables};
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

pub fn generate_rook_moves(board: &Board, tables: &RookMagicTables, moves: &mut Vec<Move>) {
    let color = board.side_to_move;
    let rooks: u64 = board.pieces(Piece::Rook, color);
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);
    let blockers = board.occupied();

    let mut bb = rooks;
    while bb != 0 {
        let from = bb.trailing_zeros() as u8;
        bb &= bb - 1;

        let mask = rook_vision_mask(from as usize);
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

pub fn generate_queen_moves(board: &Board, tables: &MagicTables, moves: &mut Vec<Move>) {
    let color = board.side_to_move;
    let queens: u64 = board.pieces(Piece::Queen, color);
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);
    let blockers = board.occupied();

    let mut bb = queens;
    while bb != 0 {
        let from = bb.trailing_zeros() as u8;
        bb &= bb - 1;

        let attacks = tables.queen_attacks(from as usize, blockers);
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

pub fn generate_king_moves(board: &Board, moves: &mut Vec<Move>) {
    let color = board.side_to_move;
    let king_bb = board.pieces(Piece::King, color);

    if king_bb == 0 {
        return; // should never happen in a legal position
    }

    let from = king_bb.trailing_zeros() as u8;

    let attacks = KING_ATTACKS[from as usize];
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);

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
