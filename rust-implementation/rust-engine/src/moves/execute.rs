use crate::board::{Board, Color, EMPTY_SQ, Piece};
use crate::moves::types::{Move, Undo};
use crate::square::Square;

/// Precomputed castling rook moves by king destination index.
#[inline(always)]
fn rook_castle_squares(king_to_idx: u8) -> Option<(Square, Square)> {
    match king_to_idx {
        6 => Some((Square::from_index(7), Square::from_index(5))), // White O-O
        2 => Some((Square::from_index(0), Square::from_index(3))), // White O-O-O
        62 => Some((Square::from_index(63), Square::from_index(61))), // Black O-O
        58 => Some((Square::from_index(56), Square::from_index(59))), // Black O-O-O
        _ => None,
    }
}

/// Helper: clear a piece bit and table entry at `idx`.
#[inline(always)]
fn remove_piece(board: &mut Board, color: Color, piece: Piece, idx: usize) {
    board.clear_square(Square::from_index(idx as u8));
    let mask = !(1u64 << idx);
    let bb = board.bb(color, piece) & mask;
    board.set_bb(color, piece, bb);
}

/// Helper: set a piece bit and table entry at `idx`.
#[inline(always)]
fn place_piece(board: &mut Board, color: Color, piece: Piece, idx: usize) {
    board.place_piece_at_sq(color, piece, Square::from_index(idx as u8));
    let mask = 1u64 << idx;
    let bb = board.bb(color, piece) | mask;
    board.set_bb(color, piece, bb);
}

pub fn make_move_basic(board: &mut Board, mv: Move) -> Undo {
    let color = board.side_to_move;
    let piece = mv.piece;
    let from_idx = mv.from.index() as usize;
    let to_idx = mv.to.index() as usize;

    // 1) Capture
    let mut capture = None;
    let occupant = board.piece_on_sq[to_idx];
    if occupant != EMPTY_SQ {
        let cap_color = Color::from_u8(occupant >> 3);
        let cap_piece = Piece::from_u8(occupant & 0b111);
        capture = Some((cap_color, cap_piece, mv.to));
        remove_piece(board, cap_color, cap_piece, to_idx);
    }

    // 2) Castling
    let castling_rook = rook_castle_squares(mv.to.index());

    // 3) Snapshot undo info
    let undo = Undo {
        from: mv.from,
        to: mv.to,
        piece,
        color,
        prev_side: color,
        capture,
        castling_rook,
    };

    // 4) Move the king
    remove_piece(board, color, piece, from_idx);
    place_piece(board, color, piece, to_idx);

    // 5) Move the rook if castling
    if let Some((rook_from, rook_to)) = castling_rook {
        let rf = rook_from.index() as usize;
        let rt = rook_to.index() as usize;
        remove_piece(board, color, Piece::Rook, rf);
        place_piece(board, color, Piece::Rook, rt);
    }

    // 6) Flip side-to-move
    board.side_to_move = color.opposite();

    undo
}

pub fn undo_move_basic(board: &mut Board, undo: Undo) {
    // 1) Restore side-to-move
    board.side_to_move = undo.prev_side;

    let from_idx = undo.from.index() as usize;
    let to_idx = undo.to.index() as usize;

    // 2) Undo king move
    remove_piece(board, undo.color, undo.piece, to_idx);
    place_piece(board, undo.color, undo.piece, from_idx);

    // 3) Undo capture
    if let Some((cap_color, cap_piece, cap_sq)) = undo.capture {
        let ci = cap_sq.index() as usize;
        place_piece(board, cap_color, cap_piece, ci);
    }

    // 4) Undo castling rook
    if let Some((rook_from, rook_to)) = undo.castling_rook {
        let rf = rook_from.index() as usize;
        let rt = rook_to.index() as usize;
        remove_piece(board, undo.color, Piece::Rook, rt);
        place_piece(board, undo.color, Piece::Rook, rf);
    }
}
