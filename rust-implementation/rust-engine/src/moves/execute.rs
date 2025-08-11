use crate::board::{Board, Color, EMPTY_SQ, Piece};
use crate::moves::types::{Move, Undo};
use crate::square::Square;

// Castling White Kingside
const CASTLE_WK: u8 = 0b0001;
// Castling White Queenside
const CASTLE_WQ: u8 = 0b0010;
// Castling Black Kingside
const CASTLE_BK: u8 = 0b0100;
// Castling Black Queenside
const CASTLE_BQ: u8 = 0b1000;

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

    let prev_en_passant = board.en_passant;
    let prev_halfmove_clock = board.halfmove_clock;
    let prev_fullmove_number = board.fullmove_number;

    // Capture
    let mut capture = None;

    if mv.is_en_passant {
        let cap_sq = if color == Color::White {
            to_idx - 8
        } else {
            to_idx + 8
        };
        capture = Some((
            color.opposite(),
            Piece::Pawn,
            Square::from_index(cap_sq as u8),
        ));
        remove_piece(board, color.opposite(), Piece::Pawn, cap_sq);
    } else {
        let occupant = board.piece_on_sq[to_idx];
        if occupant != EMPTY_SQ {
            let cap_color = Color::from_u8(occupant >> 3);
            let cap_piece = Piece::from_u8(occupant & 0b111);
            capture = Some((cap_color, cap_piece, mv.to));
            remove_piece(board, cap_color, cap_piece, to_idx);
        }
    }

    // Castling
    let castling_rook = rook_castle_squares(to_idx as u8);

    // Snapshot undo info
    let undo = Undo {
        from: mv.from,
        to: mv.to,
        piece,
        color,
        prev_side: color,
        capture,
        castling_rook,
        prev_castling_rights: board.castling_rights,
        promotion: None,
        prev_en_passant,
        prev_halfmove_clock,
        prev_fullmove_number,
    };

    match piece {
        Piece::Pawn => {
            let from_rank = from_idx / 8;
            let to_rank = to_idx / 8;
            if (color == Color::White && from_rank == 1 && to_rank == 3)
                || (color == Color::Black && from_rank == 6 && to_rank == 4)
            {
                let ep_sq = if color == Color::White {
                    from_idx + 8
                } else {
                    from_idx - 8
                };
                board.en_passant = Some(Square::from_index(ep_sq as u8));
            } else {
                board.en_passant = None;
            }
        }
        _ => {
            board.en_passant = None;
        }
    }

    // Clear castling rights if king or rook moves or rook is captured
    match piece {
        Piece::King => {
            // Clear both king- and queen-side rights for that color
            match color {
                Color::White => board.castling_rights &= !(CASTLE_WK | CASTLE_WQ), // WK | WQ
                Color::Black => board.castling_rights &= !(CASTLE_BK | CASTLE_BQ), // BK | BQ
            }
        }
        Piece::Rook => {
            match (color, mv.from.index()) {
                (Color::White, 0) => board.castling_rights &= !CASTLE_WQ, // WQ
                (Color::White, 7) => board.castling_rights &= !CASTLE_WK, // WK
                (Color::Black, 56) => board.castling_rights &= !CASTLE_BQ, // BQ
                (Color::Black, 63) => board.castling_rights &= !CASTLE_BK, // BK
                _ => {}
            }
        }
        _ => {}
    }

    // Also clear if captured a rook on its original square
    if let Some((cap_color, cap_piece, cap_sq)) = capture {
        if cap_piece == Piece::Rook {
            match (cap_color, cap_sq.index()) {
                (Color::White, 0) => board.castling_rights &= !0b0010, // WQ
                (Color::White, 7) => board.castling_rights &= !0b0001, // WK
                (Color::Black, 56) => board.castling_rights &= !0b1000, // BQ
                (Color::Black, 63) => board.castling_rights &= !0b0100, // BK
                _ => {}
            }
        }
    }

    // Move the king
    remove_piece(board, color, piece, from_idx);
    place_piece(board, color, piece, to_idx);

    // Move the rook if castling
    if let Some((rook_from, rook_to)) = castling_rook {
        let rf = rook_from.index() as usize;
        let rt = rook_to.index() as usize;
        remove_piece(board, color, Piece::Rook, rf);
        place_piece(board, color, Piece::Rook, rt);
    }

    if capture.is_some() || piece == Piece::Pawn {
        board.halfmove_clock = 0;
    } else {
        board.halfmove_clock = prev_halfmove_clock + 1;
    }
    if color == Color::Black {
        board.fullmove_number = prev_fullmove_number + 1;
    }

    // Flip side-to-move
    board.side_to_move = color.opposite();

    undo
}

pub fn undo_move_basic(board: &mut Board, undo: Undo) {
    // 1) Restore side-to-move, and castling rights
    board.side_to_move = undo.prev_side;
    board.castling_rights = undo.prev_castling_rights;
    board.en_passant = undo.prev_en_passant;
    board.halfmove_clock = undo.prev_halfmove_clock;
    board.fullmove_number = undo.prev_fullmove_number;

    let from_idx = undo.from.index() as usize;
    let to_idx = undo.to.index() as usize;

    // Undo king move
    remove_piece(board, undo.color, undo.piece, to_idx);
    place_piece(board, undo.color, undo.piece, from_idx);

    // Undo capture
    if let Some((cap_color, cap_piece, cap_sq)) = undo.capture {
        let ci = cap_sq.index() as usize;
        place_piece(board, cap_color, cap_piece, ci);
    }

    // Undo castling rook
    if let Some((rook_from, rook_to)) = undo.castling_rook {
        let rf = rook_from.index() as usize;
        let rt = rook_to.index() as usize;
        remove_piece(board, undo.color, Piece::Rook, rt);
        place_piece(board, undo.color, Piece::Rook, rf);
    }
}
