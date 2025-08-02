use crate::board::{Board, Color, EMPTY_SQ, Piece};
use crate::moves::types::{Move, Undo};

pub fn make_move_basic(board: &mut Board, mv: Move) -> Undo {
    let color = board.side_to_move;
    let piece = mv.piece;

    // Detect & clear any capture at the destination
    let to_idx = mv.to.index() as usize;
    let mut capture = None;
    let occupant = board.piece_on_sq[to_idx];
    if occupant != EMPTY_SQ {
        // Capture the piece information, create capture tuple
        let cap_color = Color::from_u8(occupant >> 3);
        let cap_piece = Piece::from_u8(occupant & 0b111);
        capture = Some((cap_color, cap_piece, mv.to));

        // Clear the square in both table & bitboard
        board.clear_square(mv.to);
        let old_cap_bb = board.bb(cap_color, cap_piece);
        board.set_bb(cap_color, cap_piece, old_cap_bb & !(1u64 << to_idx));
    }

    let undo = Undo {
        from: mv.from,
        to: mv.to,
        piece,
        color,
        prev_side: color,
        capture,
    };

    // Clear source
    board.clear_square(mv.from);
    let from_index = mv.from.index() as usize;
    let src_bb = board.bb(color, piece);
    let cleared_bb = src_bb & !(1u64 << from_index);
    board.set_bb(color, piece, cleared_bb);

    // Place at dest
    board.place_piece_at_sq(color, piece, mv.to);
    let to_index = mv.to.index() as usize;
    let dst_bb = board.bb(color, piece);
    let updated_bb = dst_bb | (1u64 << to_index);
    board.set_bb(color, piece, updated_bb);

    // Flip side
    board.side_to_move = color.opposite();

    undo
}

pub fn undo_move_basic(board: &mut Board, undo: Undo) {
    board.side_to_move = undo.prev_side;

    // Remove from dest
    board.clear_square(undo.to);
    let to_index = undo.to.index() as usize;
    let dst_bb = board.bb(undo.color, undo.piece);
    let cleared_bb = dst_bb & !(1u64 << to_index);
    board.set_bb(undo.color, undo.piece, cleared_bb);

    // 2) Restore piece to the source square
    board.place_piece_at_sq(undo.color, undo.piece, undo.from);
    let from_index = undo.from.index() as usize;
    let src_bb = board.bb(undo.color, undo.piece);
    let restored_bb = src_bb | (1u64 << from_index);
    board.set_bb(undo.color, undo.piece, restored_bb);

    // If there was a capture, put that piece back
    if let Some((cap_color, cap_piece, cap_sq)) = undo.capture {
        let cap_idx = cap_sq.index() as usize;
        board.place_piece_at_sq(cap_color, cap_piece, cap_sq);
        let cap_bb = board.bb(cap_color, cap_piece);
        board.set_bb(cap_color, cap_piece, cap_bb | (1u64 << cap_idx));
    }
}
