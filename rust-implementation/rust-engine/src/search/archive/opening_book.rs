use crate::board::{Board, Piece};
use crate::moves::types::Move;
use crate::square::Square;
use rand::Rng;
use std::fs::File;
use std::io::{BufReader, Read};
use std::path::Path;

pub struct OpeningBook {
    entries: Vec<BookEntry>,
}

struct BookEntry {
    key: u64,       // Zobrist hash
    move_data: u16, // Encoded move
    weight: u16,    // Move quality
    learn: u32,     // Unused
}

impl OpeningBook {
    /// Load a Polyglot opening book from disk
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self, std::io::Error> {
        let file = File::open(path)?;
        let mut reader = BufReader::new(file);
        let mut entries = Vec::new();

        // Each entry is exactly 16 bytes
        let mut buffer = [0u8; 16];

        while reader.read_exact(&mut buffer).is_ok() {
            // Parse big-endian values
            let key = u64::from_be_bytes([
                buffer[0], buffer[1], buffer[2], buffer[3], buffer[4], buffer[5], buffer[6],
                buffer[7],
            ]);

            let move_data = u16::from_be_bytes([buffer[8], buffer[9]]);
            let weight = u16::from_be_bytes([buffer[10], buffer[11]]);
            let learn = u32::from_be_bytes([buffer[12], buffer[13], buffer[14], buffer[15]]);

            entries.push(BookEntry {
                key,
                move_data,
                weight,
                learn,
            });
        }

        // CRITICAL: Sort by key for binary search
        entries.sort_by_key(|e| e.key);

        println!("Loaded {} book positions", entries.len());

        Ok(OpeningBook { entries })
    }

    /// Get a move from the book for the current position
    pub fn probe(&self, board: &Board) -> Option<Move> {
        let hash = board.zobrist;

        // Binary search for this position
        let idx = match self.entries.binary_search_by_key(&hash, |e| e.key) {
            Ok(i) => i,
            Err(_) => return None, // Position not in book
        };

        // Multiple moves may exist for same position
        // Find all matching entries
        let mut moves = Vec::new();
        let mut i = idx;

        // Search backward to find first entry with this hash
        while i > 0 && self.entries[i - 1].key == hash {
            i -= 1;
        }

        // Collect all entries with this hash
        while i < self.entries.len() && self.entries[i].key == hash {
            moves.push(&self.entries[i]);
            i += 1;
        }

        if moves.is_empty() {
            return None;
        }

        // Choose move weighted by quality
        // Higher weight = more likely to be chosen
        self.select_weighted_move(&moves, board)
    }

    fn select_weighted_move(&self, moves: &[&BookEntry], board: &Board) -> Option<Move> {
        // Calculate total weight
        let total_weight: u32 = moves.iter().map(|e| e.weight as u32).sum();

        if total_weight == 0 {
            // If all weights are 0, pick randomly
            let mut rng = rand::rng();
            let random_index: usize = rng.random_range(0..moves.len());
            return Some(self.decode_move(moves[random_index].move_data, board));
        }

        // Pick a random value in range [0, total_weight)
        let mut random_value = rand::random::<u32>() % total_weight;

        // Select move based on weight
        for entry in moves {
            if random_value < entry.weight as u32 {
                return Some(self.decode_move(entry.move_data, board));
            }
            random_value -= entry.weight as u32;
        }

        // Fallback (shouldn't happen)
        Some(self.decode_move(moves[0].move_data, board))
    }

    fn decode_move(&self, move_data: u16, board: &Board) -> Move {
        // Polyglot move encoding:
        // Bits 0-5:   from square (0-63)
        // Bits 6-11:  to square (0-63)
        // Bits 12-14: promotion piece (0=none, 1=N, 2=B, 3=R, 4=Q)

        let from_sq = (move_data & 0x3F) as u8;
        let to_sq = ((move_data >> 6) & 0x3F) as u8;
        let promo_code = (move_data >> 12) & 0x7;

        let from = Square::from_index(from_sq);
        let to = Square::from_index(to_sq);

        // Determine promotion piece
        let promotion = match promo_code {
            1 => Some(Piece::Knight),
            2 => Some(Piece::Bishop),
            3 => Some(Piece::Rook),
            4 => Some(Piece::Queen),
            _ => None,
        };

        // Get the piece that's moving
        let piece = board
            .piece_type_at(from)
            .expect("Book move from empty square!");

        // Calculate move flags (capture, en passant, castling, etc.)
        let flags = self.calculate_flags(board, from, to, piece, promotion);

        Move {
            from,
            to,
            piece,
            promotion,
            flags,
        }
    }

    fn calculate_flags(
        &self,
        board: &Board,
        from: Square,
        to: Square,
        piece: Piece,
        promotion: Option<Piece>,
    ) -> u8 {
        let mut flags = 0u8;

        // Check if it's a capture
        if board.piece_at(to).is_some() {
            flags |= 0b0100; // Capture flag
        }

        // Check for special pawn moves
        if piece == Piece::Pawn {
            // Double push
            let from_rank = from.rank();
            let to_rank = to.rank();
            if (from_rank as i8 - to_rank as i8).abs() == 2 {
                flags |= 0b0001; // Double pawn push
            }

            // En passant
            if let Some(ep_sq) = board.en_passant {
                if ep_sq == to && board.piece_at(to).is_none() {
                    flags |= 0b0101; // En passant capture
                }
            }

            // Promotion
            if promotion.is_some() {
                flags |= 0b1000; // Promotion flag
            }
        }

        // Check for castling
        if piece == Piece::King {
            let from_file = from.file();
            let to_file = to.file();

            if (from_file as i8 - to_file as i8).abs() == 2 {
                flags |= 0b0010; // Castling flag
            }
        }

        flags
    }
}
