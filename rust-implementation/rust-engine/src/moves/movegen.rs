use crate::board::{Board, Color, Piece};
use crate::moves::king::KING_ATTACKS;
use crate::moves::knight::KNIGHT_ATTACKS;
use crate::moves::magic::MagicTables;
use crate::moves::magic::masks::{bishop_vision_mask, rook_vision_mask};
use crate::moves::magic::structs::{BishopMagicTables, RookMagicTables};
use crate::moves::pawn::{BLACK_PAWN_ATTACKS, WHITE_PAWN_ATTACKS};
use crate::moves::square_control::is_legal_castling;
use crate::moves::types::Move;
use crate::square::Square;
use crate::utils::pop_lsb;

// Predefined Rank Constants
const RANK1: u64 = 0x0000_0000_0000_00FF;
const RANK2: u64 = 0x0000_0000_0000_FF00;
const RANK7: u64 = 0x00FF_0000_0000_0000;
const RANK8: u64 = 0xFF00_0000_0000_0000;

// Castling Constants
const WHITE_KINGSIDE_BETWEEN: u64 = 0x0000_0000_0000_0060;
const WHITE_QUEENSIDE_BETWEEN: u64 = 0x0000_0000_0000_000E;
const BLACK_KINGSIDE_BETWEEN: u64 = 0x6000_0000_0000_0000;
const BLACK_QUEENSIDE_BETWEEN: u64 = 0x0E00_0000_0000_0000;

// Promotion Array
const PROMOS: [Piece; 4] = [Piece::Queen, Piece::Rook, Piece::Bishop, Piece::Knight];

/// Helper functionality to push latest found move
#[inline(always)]
fn push_piece_moves(
    from: u8,
    mut targets: u64,
    enemy: u64,
    move_piece: Piece,
    move_list: &mut Vec<Move>,
) {
    while targets != 0 {
        let to = pop_lsb(&mut targets);
        move_list.push(Move {
            from: Square::from_index(from),
            to: Square::from_index(to),
            piece: move_piece,
            promotion: None,
            is_capture: (enemy >> to) & 1 != 0,
            is_en_passant: false,
            is_castling: false,
        });
    }
}

/// Function to determine which squares to check for kingside castling
#[inline(always)]
fn kingside_between(color: Color) -> u64 {
    match color {
        Color::White => WHITE_KINGSIDE_BETWEEN,
        Color::Black => BLACK_KINGSIDE_BETWEEN,
    }
}

/// Function to determine which squares to check for queenside castling
#[inline(always)]
fn queenside_between(color: Color) -> u64 {
    match color {
        Color::White => WHITE_QUEENSIDE_BETWEEN,
        Color::Black => BLACK_QUEENSIDE_BETWEEN,
    }
}

pub fn generate_knight_moves(board: &Board, move_list: &mut Vec<Move>) {
    let color = board.side_to_move;
    let knights = board.pieces(Piece::Knight, color);
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);

    let mut bb = knights;
    while bb != 0 {
        let from = pop_lsb(&mut bb);
        let targets = KNIGHT_ATTACKS[from as usize] & !friendly;
        push_piece_moves(from, targets, enemy, Piece::Knight, move_list);
    }
}

pub fn generate_bishop_moves(board: &Board, tables: &BishopMagicTables, move_list: &mut Vec<Move>) {
    let color = board.side_to_move;
    let bishops = board.pieces(Piece::Bishop, color);
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);
    let blockers = board.occupied();

    let mut bb = bishops;
    while bb != 0 {
        let from = pop_lsb(&mut bb);
        let mask = bishop_vision_mask(from as usize);
        let attacks = tables.get_attacks(from as usize, blockers, mask);
        let targets = attacks & !friendly;
        push_piece_moves(from, targets, enemy, Piece::Bishop, move_list);
    }
}

pub fn generate_rook_moves(board: &Board, tables: &RookMagicTables, move_list: &mut Vec<Move>) {
    let color = board.side_to_move;
    let rooks: u64 = board.pieces(Piece::Rook, color);
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);
    let blockers = board.occupied();

    let mut bb = rooks;
    while bb != 0 {
        let from = pop_lsb(&mut bb);
        let mask = rook_vision_mask(from as usize);
        let attacks = tables.get_attacks(from as usize, blockers, mask);
        let targets = attacks & !friendly;
        push_piece_moves(from, targets, enemy, Piece::Rook, move_list);
    }
}

pub fn generate_queen_moves(board: &Board, tables: &MagicTables, move_list: &mut Vec<Move>) {
    let color = board.side_to_move;
    let queens: u64 = board.pieces(Piece::Queen, color);
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);
    let blockers = board.occupied();

    let mut bb = queens;
    while bb != 0 {
        let from = pop_lsb(&mut bb);
        let attacks = tables.queen_attacks(from as usize, blockers);
        let targets = attacks & !friendly;
        push_piece_moves(from, targets, enemy, Piece::Queen, move_list);
    }
}

pub fn generate_king_moves(board: &Board, tables: &MagicTables, move_list: &mut Vec<Move>) {
    let color = board.side_to_move;
    let king_bb = board.pieces(Piece::King, color);

    if king_bb == 0 {
        return;
    } // illegal position safeguard

    let from = king_bb.trailing_zeros() as u8; // only one king
    let friendly = board.occupancy(color);
    let enemy = board.opponent_occupancy(color);

    let targets = KING_ATTACKS[from as usize] & !friendly;
    push_piece_moves(from, targets, enemy, Piece::King, move_list);

    let occ = board.occupied();

    // King-side castle
    if board.has_kingside_castle(color) && (occ & kingside_between(color)) == 0 {
        let mv = Move {
            from: Square::from_index(from),
            to: Square::from_index(from + 2), // g-file
            piece: Piece::King,
            promotion: None,
            is_capture: false,
            is_en_passant: false,
            is_castling: true,
        };

        if is_legal_castling(board, mv, tables) {
            move_list.push(mv);
        }
    }

    // Queen-side castle
    if board.has_queenside_castle(color) && (occ & queenside_between(color)) == 0 {
        move_list.push(Move {
            from: Square::from_index(from),
            to: Square::from_index(from - 2), // c-file
            piece: Piece::King,
            promotion: None,
            is_capture: false,
            is_en_passant: false,
            is_castling: true,
        });
    }
}

pub fn generate_pawn_moves(board: &Board, move_list: &mut Vec<Move>) {
    let color = board.side_to_move;
    let pawns = board.pieces(Piece::Pawn, color);
    let enemy = board.opponent_occupancy(color);
    let empty = !board.occupied();

    // Rank masks
    let (start_rank, promo_rank, push_up) = match color {
        Color::White => (RANK7, RANK8, 8i8),
        Color::Black => (RANK2, RANK1, -8i8),
    };

    // Single accessor that captures `color` (one closure type)
    let pawn_attacks = |sq: usize| -> u64 {
        match color {
            Color::White => WHITE_PAWN_ATTACKS[sq],
            Color::Black => BLACK_PAWN_ATTACKS[sq],
        }
    };

    // ===== 1) Quiet single pushes (exclude promotion rank) =====
    let single_pushes = match color {
        Color::White => ((pawns << 8) & empty) & !promo_rank,
        Color::Black => ((pawns >> 8) & empty) & !promo_rank,
    };
    let mut bb = single_pushes;
    while bb != 0 {
        let to = pop_lsb(&mut bb);
        let from = match color {
            Color::White => to - 8,
            Color::Black => to + 8,
        };
        debug_assert!(from < 64 && to < 64);
        move_list.push(Move {
            from: Square::from_index(from),
            to: Square::from_index(to),
            piece: Piece::Pawn,
            promotion: None,
            is_capture: false,
            is_en_passant: false,
            is_castling: false,
        });
    }

    // ===== 2) Quiet double pushes =====
    let double_pushes = match color {
        Color::White => (((pawns & RANK2) << 8) & empty) << 8 & empty,
        Color::Black => (((pawns & RANK7) >> 8) & empty) >> 8 & empty,
    };
    let mut bb = double_pushes;
    while bb != 0 {
        let to = pop_lsb(&mut bb);
        let from = match color {
            Color::White => to - 16,
            Color::Black => to + 16,
        };
        debug_assert!(from < 64 && to < 64);
        move_list.push(Move {
            from: Square::from_index(from),
            to: Square::from_index(to),
            piece: Piece::Pawn,
            promotion: None,
            is_capture: false,
            is_en_passant: false,
            is_castling: false,
        });
    }

    // ===== 3) Normal captures (exclude promotion targets) =====
    let mut attackers = pawns;
    while attackers != 0 {
        let from = pop_lsb(&mut attackers);
        let targets = pawn_attacks(from as usize) & enemy & !promo_rank;
        let mut t = targets;
        while t != 0 {
            let to = pop_lsb(&mut t);
            move_list.push(Move {
                from: Square::from_index(from),
                to: Square::from_index(to),
                piece: Piece::Pawn,
                promotion: None,
                is_capture: true,
                is_en_passant: false,
                is_castling: false,
            });
        }
    }

    // ===== 4) Promotion pushes =====
    let shift = push_up.unsigned_abs();
    let promo_pushes = if push_up > 0 {
        (pawns & start_rank) << shift & empty
    } else {
        (pawns & start_rank) >> shift & empty
    };
    let mut bb = promo_pushes;
    while bb != 0 {
        let to = pop_lsb(&mut bb);
        let from = if push_up > 0 { to - shift } else { to + shift };
        for &promo in PROMOS.iter() {
            move_list.push(Move {
                from: Square::from_index(from),
                to: Square::from_index(to),
                piece: Piece::Pawn,
                promotion: Some(promo),
                is_capture: false,
                is_en_passant: false,
                is_castling: false,
            });
        }
    }

    // ===== 5) Promotion captures =====
    let mut promo_attackers = pawns & start_rank;
    while promo_attackers != 0 {
        let from = pop_lsb(&mut promo_attackers);
        let targets = pawn_attacks(from as usize) & enemy & promo_rank;
        let mut t = targets;
        while t != 0 {
            let to = pop_lsb(&mut t);
            for &promo in PROMOS.iter() {
                move_list.push(Move {
                    from: Square::from_index(from),
                    to: Square::from_index(to),
                    piece: Piece::Pawn,
                    promotion: Some(promo),
                    is_capture: true,
                    is_en_passant: false,
                    is_castling: false,
                });
            }
        }
    }

    // ===== 6) En passant (sanity-checked pseudo-legal) =====
    if let Some(ep_sq) = board.en_passant {
        let ep = ep_sq.index();
        if (empty & (1u64 << ep)) != 0 {
            let cap_sq = match color {
                Color::White => ep - 8,
                Color::Black => ep + 8,
            };
            let enemy_pawns = board.pieces(Piece::Pawn, color.opposite());
            if (enemy_pawns & (1u64 << cap_sq)) != 0 {
                let mut atk = pawns;
                while atk != 0 {
                    let from = pop_lsb(&mut atk);
                    if (pawn_attacks(from as usize) & (1u64 << ep)) != 0 {
                        move_list.push(Move {
                            from: Square::from_index(from),
                            to: Square::from_index(ep),
                            piece: Piece::Pawn,
                            promotion: None,
                            is_capture: true,
                            is_en_passant: true,
                            is_castling: false,
                        });
                    }
                }
            }
        }
    }
}

pub fn generate_pseudo_legal(board: &Board, tables: &MagicTables, moves: &mut Vec<Move>) {
    moves.clear();
    generate_pawn_moves(board, moves);
    generate_knight_moves(board, moves);
    generate_bishop_moves(board, &tables.bishop, moves);
    generate_rook_moves(board, &tables.rook, moves);
    generate_queen_moves(board, tables, moves);
    generate_king_moves(board, tables, moves);
}
