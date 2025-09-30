use crate::board::{Board, Color, EMPTY_SQ, Piece};
use crate::hash::zobrist::{ep_file_to_hash, xor_castling_rights_delta, zobrist_keys};
use crate::moves::magic::MagicTables;
use crate::moves::movegen::generate_pseudo_legal;
use crate::moves::square_control::{in_check, is_legal_castling};
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

const FILE_A: u64 = 0x0101_0101_0101_0101;
const FILE_H: u64 = 0x8080_8080_8080_8080;

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

#[inline(always)]
fn rights_mask_to_clear_for_rook(color: Color, rook_sq: u8) -> u8 {
    match (color, rook_sq) {
        (Color::White, 0) => CASTLE_WQ,  // a1
        (Color::White, 7) => CASTLE_WK,  // h1
        (Color::Black, 56) => CASTLE_BQ, // a8
        (Color::Black, 63) => CASTLE_BK, // h8
        _ => 0,
    }
}

/// Helper: clear a piece bit and table entry at `idx`.
#[inline(always)]
fn remove_piece(board: &mut Board, color: Color, piece: Piece, idx: usize) {
    let new_bb = board.bb(color, piece) & !(1u64 << idx);
    board.set_bb(color, piece, new_bb);
}

/// Helper: set a piece bit and table entry at `idx`.
#[inline(always)]
fn place_piece(board: &mut Board, color: Color, piece: Piece, idx: usize) {
    let new_bb = board.bb(color, piece) | (1u64 << idx);
    board.set_bb(color, piece, new_bb);
}

pub fn make_move_basic(board: &mut Board, mv: Move) -> Undo {
    let color = board.side_to_move;
    let piece = mv.piece;
    let from_idx = mv.from.index() as usize;
    let to_idx = mv.to.index() as usize;

    let prev_en_passant = board.en_passant;

    // If an EP file was in the hash (relaxed rule), XOR it OUT now (pre-move, pre-flip)
    if let Some(f) = ep_file_to_hash(board) {
        board.zobrist ^= zobrist_keys().ep_file[f as usize];
    }

    board.en_passant = None;
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
    // let castling_rook: Option<(Square, Square)> = rook_castle_squares(to_idx as u8);

    // Snapshot undo info
    let mut undo = Undo {
        from: mv.from,
        to: mv.to,
        piece,
        color,
        prev_side: color,
        capture,
        castling_rook: None,
        prev_castling_rights: board.castling_rights,
        promotion: None,
        prev_en_passant,
        prev_halfmove_clock,
        prev_fullmove_number,
    };

    let old_rights = board.castling_rights;

    if mv.is_castling {
        if let Some((rf, rt)) = rook_castle_squares(to_idx as u8) {
            undo.castling_rook = Some((rf, rt));
        }
    } else {
        undo.castling_rook = None;
    }

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
                // Only keep EP if capturable by the opponent (next side to move)
                let ep_sq_u8 = ep_sq as u8;
                let bb_s = 1u64 << ep_sq_u8;

                let opponent = color.opposite();
                let has_attacker = if opponent == Color::White {
                    // White sources that attack INTO ep_sq
                    let src_ne = (bb_s >> 9) & !FILE_H;
                    let src_nw = (bb_s >> 7) & !FILE_A;
                    ((src_ne | src_nw) & board.bb(Color::White, Piece::Pawn)) != 0
                } else {
                    // Black sources that attack INTO ep_sq
                    let src_se = (bb_s << 7) & !FILE_A;
                    let src_sw = (bb_s << 9) & !FILE_H;
                    ((src_se | src_sw) & board.bb(Color::Black, Piece::Pawn)) != 0
                };

                if has_attacker {
                    let f = (ep_sq_u8 % 8) as usize;
                    board.zobrist ^= zobrist_keys().ep_file[f];
                }

                // ── ADD THIS DEBUG INVARIANT ─────────────────────────────────────────
                let ep_rank = ep_sq / 8; // 0-based ranks: 0=rank1 … 7=rank8
                debug_assert!(
                    (color == Color::White && ep_rank == 2)   // EP must be on rank 3 after white double push
                || (color == Color::Black && ep_rank == 5), // EP must be on rank 6 after black double push
                    "EP square on wrong rank: {:?} (ep_rank={}, color={:?})",
                    Square::from_index(ep_sq as u8),
                    ep_rank,
                    color
                );
                // ────────────────────────────────────────────────────────────────────
            }
        }
        _ => {}
    }

    // Compute all rights to clear for this move
    let mut mask_to_clear: u8 = 0;

    // (i) King moved → clear both for that color
    if piece == Piece::King {
        mask_to_clear |= match color {
            Color::White => CASTLE_WK | CASTLE_WQ,
            Color::Black => CASTLE_BK | CASTLE_BQ,
        };
    }

    // (ii) Rook moved from a corner → clear that side's right
    if piece == Piece::Rook {
        mask_to_clear |= rights_mask_to_clear_for_rook(color, mv.from.index());
    }

    // (iii) Captured a rook on its original corner → clear that side's right
    if let Some((cap_color, cap_piece, cap_sq)) = capture {
        if cap_piece == Piece::Rook {
            mask_to_clear |= rights_mask_to_clear_for_rook(cap_color, cap_sq.index());
        }
    }

    // Apply rights change ONCE and update hash via delta
    let new_rights = old_rights & !mask_to_clear;
    if new_rights != old_rights {
        board.castling_rights = new_rights;
        xor_castling_rights_delta(&mut board.zobrist, zobrist_keys(), old_rights, new_rights);
    }

    // Move the king
    remove_piece(board, color, piece, from_idx);

    if let Some(prom) = mv.promotion {
        debug_assert!(piece == Piece::Pawn, "Only pawns can promote");
        place_piece(board, color, prom, to_idx);
        undo.promotion = Some(prom);
    } else {
        // Normal (non-promotion) move
        place_piece(board, color, piece, to_idx);
    }

    // Move the rook if castling
    if let Some((rook_from, rook_to)) = undo.castling_rook {
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
    board.zobrist ^= zobrist_keys().side_to_move;

    #[cfg(debug_assertions)]
    board.assert_hash();

    undo
}

pub fn undo_move_basic(board: &mut Board, undo: Undo) {
    // If the current position has an EP file included, XOR it OUT first (pre-flip)
    if let Some(f) = ep_file_to_hash(board) {
        board.zobrist ^= zobrist_keys().ep_file[f as usize];
    }

    // ---- Flip side back (hash + state) ----
    board.zobrist ^= zobrist_keys().side_to_move;
    board.side_to_move = undo.prev_side;

    // ---- Castling rights: apply HASH DELTA (cur -> prev), then assign ----
    let kz = zobrist_keys();
    let cur = board.castling_rights;
    let prev = undo.prev_castling_rights;
    if cur != prev {
        xor_castling_rights_delta(&mut board.zobrist, kz, cur, prev);
        board.castling_rights = prev;
    } else {
        // keep them equal explicitly (no hash change)
        board.castling_rights = prev;
    }

    // ---- Restore clocks ----
    board.halfmove_clock = undo.prev_halfmove_clock;
    board.fullmove_number = undo.prev_fullmove_number;

    let from_idx = undo.from.index() as usize;
    let to_idx = undo.to.index() as usize;

    // ---- Undo the moved piece (and promotion if any) ----
    if let Some(prom) = undo.promotion {
        // The piece on 'to' is the promoted piece; remove it, restore a pawn at 'from'
        remove_piece(board, undo.color, prom, to_idx);
        place_piece(board, undo.color, Piece::Pawn, from_idx);
    } else {
        // Normal move back
        remove_piece(board, undo.color, undo.piece, to_idx);
        place_piece(board, undo.color, undo.piece, from_idx);
    }

    // ---- Undo capture (including EP capture, since undo.capture holds the pawn's square) ----
    if let Some((cap_color, cap_piece, cap_sq)) = undo.capture {
        let ci = cap_sq.index() as usize;
        place_piece(board, cap_color, cap_piece, ci);
    }

    // ---- Undo castling rook, if this was a castle ----
    if let Some((rook_from, rook_to)) = undo.castling_rook {
        let rf = rook_from.index() as usize;
        let rt = rook_to.index() as usize;
        remove_piece(board, undo.color, Piece::Rook, rt);
        place_piece(board, undo.color, Piece::Rook, rf);
    }

    // ---- Restore prior EP square and, if it now contributes, XOR it IN ----
    board.en_passant = undo.prev_en_passant;
    if let Some(f) = ep_file_to_hash(board) {
        board.zobrist ^= kz.ep_file[f as usize];
    }

    #[cfg(debug_assertions)]
    board.assert_hash();
}

pub fn generate_legal(board: &mut Board, tables: &MagicTables, moves: &mut Vec<Move>) {
    let mut pseudo = Vec::new();
    generate_pseudo_legal(board, tables, &mut pseudo);

    moves.clear();

    for mv in pseudo {
        if mv.is_castling && !is_legal_castling(board, mv, tables) {
            continue;
        }
        let mover = board.side_to_move;
        let undo = make_move_basic(board, mv);
        let illegal = in_check(board, mover, tables);
        undo_move_basic(board, undo);
        if !illegal {
            moves.push(mv);
        }
    }
}
