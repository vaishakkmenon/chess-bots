use super::{Board, CASTLE_BK, CASTLE_BQ, CASTLE_WK, CASTLE_WQ, Color, Piece};
use crate::square::Square;

static PIECE_TABLE: [(Piece, Color, char); 12] = [
    (Piece::Rook, Color::Black, 'r'),
    (Piece::Knight, Color::Black, 'n'),
    (Piece::Bishop, Color::Black, 'b'),
    (Piece::Queen, Color::Black, 'q'),
    (Piece::King, Color::Black, 'k'),
    (Piece::Pawn, Color::Black, 'p'),
    (Piece::Rook, Color::White, 'R'),
    (Piece::Knight, Color::White, 'N'),
    (Piece::Bishop, Color::White, 'B'),
    (Piece::Queen, Color::White, 'Q'),
    (Piece::King, Color::White, 'K'),
    (Piece::Pawn, Color::White, 'P'),
];

impl Board {
    /// Generate the piece‐placement portion of FEN (e.g., "rnbqkbnr/pppppppp/8/...").
    pub(crate) fn placement_fen(&self) -> String {
        let mut fen = String::new();

        for rank in (0..8).rev() {
            let mut empty = 0;
            for file in 0..8 {
                let idx = rank * 8 + file;
                let bit = 1u64 << idx;

                // find the piece symbol, if any
                if let Some(symbol) = PIECE_TABLE.iter().find_map(|&(piece, color, sym)| {
                    if self.bb(color, piece) & bit != 0 {
                        Some(sym)
                    } else {
                        None
                    }
                }) {
                    // flush empty counter
                    if empty > 0 {
                        fen.push_str(&empty.to_string());
                        empty = 0;
                    }
                    fen.push(symbol);
                } else {
                    empty += 1;
                }
            }

            // trailing empties
            if empty > 0 {
                fen.push_str(&empty.to_string());
            }
            if rank > 0 {
                fen.push('/');
            }
        }

        fen
    }

    pub fn castling_fen(&self) -> String {
        let mut s = String::new();

        if self.has_castling(CASTLE_WK) {
            s.push('K');
        }
        if self.has_castling(CASTLE_WQ) {
            s.push('Q');
        }
        if self.has_castling(CASTLE_BK) {
            s.push('k');
        }
        if self.has_castling(CASTLE_BQ) {
            s.push('q');
        }

        if s.is_empty() {
            s.push('-');
        }

        s
    }

    pub fn en_passant_fen(&self) -> String {
        match self.en_passant {
            Some(sq) => sq.to_string(),
            None => "-".to_string(),
        }
    }

    pub fn to_fen(&self) -> String {
        format!(
            "{} {} {} {} {} {}",
            self.placement_fen(),
            if self.side_to_move == Color::White {
                'w'
            } else {
                'b'
            },
            self.castling_fen(),
            self.en_passant_fen(),
            self.halfmove_clock,
            self.fullmove_number,
        )
    }

    pub(crate) fn parse_placement(&mut self, placement: &str) -> Result<(), String> {
        *self = Board::new_empty(); // reset the board
        let ranks: Vec<&str> = placement.split('/').collect();
        if ranks.len() != 8 {
            return Err(format!("Expected 8 ranks, got {}", ranks.len()));
        }
        for (i, &rank_str) in ranks.iter().enumerate() {
            let rank = 7 - i;
            self.parse_rank(rank, rank_str)?; // call the method on `self`
        }
        Ok(())
    }

    fn parse_rank(&mut self, rank: usize, rank_str: &str) -> Result<(), String> {
        let mut file = 0u8;
        for ch in rank_str.chars() {
            if file >= 8 {
                return Err(format!(
                    "Too many squares on rank {}: {}",
                    8 - rank,
                    rank_str
                ));
            }
            if let Some(skip) = ch.to_digit(10) {
                // Digit: skip that many empty files
                file = file
                    .checked_add(skip as u8)
                    .ok_or_else(|| format!("Invalid skip {} on rank {}", skip, rank))?;
            } else {
                // Letter: set a piece at (rank, file)
                let idx = rank * 8 + file as usize;
                self.set_piece_at(ch, idx)?;
                file += 1;
            }
        }
        if file != 8 {
            return Err(format!(
                "Not enough squares on rank {}: {}",
                8 - rank,
                rank_str
            ));
        }
        Ok(())
    }

    /// Place a piece on `idx` (0–63) based on its FEN character.
    fn set_piece_at(&mut self, ch: char, idx: usize) -> Result<(), String> {
        let mask = 1u64 << idx;
        // Map FEN char → (Color, Piece)
        let (color, piece) = match ch {
            'P' => (Color::White, Piece::Pawn),
            'N' => (Color::White, Piece::Knight),
            'B' => (Color::White, Piece::Bishop),
            'R' => (Color::White, Piece::Rook),
            'Q' => (Color::White, Piece::Queen),
            'K' => (Color::White, Piece::King),
            'p' => (Color::Black, Piece::Pawn),
            'n' => (Color::Black, Piece::Knight),
            'b' => (Color::Black, Piece::Bishop),
            'r' => (Color::Black, Piece::Rook),
            'q' => (Color::Black, Piece::Queen),
            'k' => (Color::Black, Piece::King),
            _ => return Err(format!("Invalid piece char '{}'", ch)),
        };

        // Grab old bitboard, OR in the mask, and let set_bb update occ_* for us
        let old_bb = self.bb(color, piece);
        self.set_bb(color, piece, old_bb | mask);
        Ok(())
    }

    pub(crate) fn parse_active_color(&mut self, field: &str) -> Result<(), String> {
        self.side_to_move = match field {
            "w" => Color::White,
            "b" => Color::Black,
            _ => return Err(format!("Invalid active-color in FEN: `{}`", field)),
        };
        Ok(())
    }

    /// Parse the castling-rights field (e.g. "KQkq" or "-") and update `self.castling_rights`.
    pub(crate) fn parse_castling_rights(&mut self, field: &str) -> Result<(), String> {
        self.castling_rights = 0;

        if field == "-" {
            return Ok(());
        }

        for c in field.chars() {
            match c {
                'K' => self.castling_rights |= CASTLE_WK,
                'Q' => self.castling_rights |= CASTLE_WQ,
                'k' => self.castling_rights |= CASTLE_BK,
                'q' => self.castling_rights |= CASTLE_BQ,
                _ => {
                    return Err(format!("Invalid castling-rights character `{}`", c));
                }
            }
        }
        Ok(())
    }

    /// Parse the en_passant field, is it a valid square or empty
    pub(crate) fn parse_en_passant(&mut self, field: &str) -> Result<(), String> {
        self.en_passant = if field == "-" {
            None
        } else {
            let sq = field
                .parse::<Square>()
                .map_err(|e| format!("Invalid en-passant square `{}`: {}", field, e))?;
            Some(sq)
        };
        Ok(())
    }

    /// Parse the halfmove and fullmove clock fields.
    pub(crate) fn parse_clocks(
        &mut self,
        halfmove_s: &str,
        fullmove_s: &str,
    ) -> Result<(), String> {
        let halfmove: u32 = halfmove_s
            .parse()
            .map_err(|_| format!("Invalid halfmove clock `{}`", halfmove_s))?;

        let fullmove: u32 = fullmove_s
            .parse()
            .map_err(|_| format!("Invalid fullmove number `{}`", fullmove_s))?;

        if fullmove < 1 {
            return Err(format!(
                "Invalid fullmove number `{}`: must be >= 1",
                fullmove
            ));
        }

        self.halfmove_clock = halfmove;
        self.fullmove_number = fullmove;

        Ok(())
    }

    /// Parse a FEN string and update this board’s state.
    pub fn set_fen(&mut self, fen: &str) -> Result<(), String> {
        // 1. Split into six FEN fields
        let (placement, active, castling, ep, hm, fm) = Board::split_fen(fen)?;

        // 2. Parse each field in turn
        self.parse_placement(placement)?;
        self.parse_active_color(active)?;
        self.parse_castling_rights(castling)?;
        self.parse_en_passant(ep)?;
        self.parse_clocks(hm, fm)?;

        Ok(())
    }

    /// Split into six fields, validate count
    pub(crate) fn split_fen(fen: &str) -> Result<(&str, &str, &str, &str, &str, &str), String> {
        let p: Vec<&str> = fen.split_whitespace().collect();
        if p.len() != 6 {
            return Err(format!("Expected 6 FEN fields, found {}", p.len()));
        }
        Ok((p[0], p[1], p[2], p[3], p[4], p[5]))
    }
}
