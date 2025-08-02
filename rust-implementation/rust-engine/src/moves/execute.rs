use crate::board::Board;
use crate::moves::types::{Move, Undo};

pub fn make_move_basic(board: &mut Board, mv: Move) -> Undo {
    let color = board.side_to_move;
    let piece = mv.piece;

    let undo = Undo {
        from: mv.from,
        to: mv.to,
        piece,
        color,
        prev_side: color,
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
}
