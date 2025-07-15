use super::{Board, CASTLE_BK, CASTLE_BQ, CASTLE_WK, CASTLE_WQ, Color};
use crate::square::Square;

impl Board {
    /// Generate the piece‐placement portion of FEN (e.g., "rnbqkbnr/pppppppp/8/...").
    pub(crate) fn placement_fen(&self) -> String {
        let mut fen = String::new();

        // Loop ranks 8 down to 1 (rank_idx 7 → 0)
        for rank in (0..8).rev() {
            let mut empty = 0;

            // Loop files a through h (file_idx 0 → 7)
            for file in 0..8 {
                let idx = rank * 8 + file;
                let bit = 1u64 << idx;

                // Determine which piece (if any) occupies this square:
                let piece_char = if self.white_pawns & bit != 0 {
                    Some('P')
                } else if self.white_knights & bit != 0 {
                    Some('N')
                } else if self.white_bishops & bit != 0 {
                    Some('B')
                } else if self.white_rooks & bit != 0 {
                    Some('R')
                } else if self.white_queens & bit != 0 {
                    Some('Q')
                } else if self.white_king & bit != 0 {
                    Some('K')
                } else if self.black_pawns & bit != 0 {
                    Some('p')
                } else if self.black_knights & bit != 0 {
                    Some('n')
                } else if self.black_bishops & bit != 0 {
                    Some('b')
                } else if self.black_rooks & bit != 0 {
                    Some('r')
                } else if self.black_queens & bit != 0 {
                    Some('q')
                } else if self.black_king & bit != 0 {
                    Some('k')
                } else {
                    None
                };

                if let Some(ch) = piece_char {
                    // Flush any accumulated empties
                    if empty > 0 {
                        fen.push_str(&empty.to_string());
                        empty = 0;
                    }
                    fen.push(ch);
                } else {
                    // Empty square
                    empty += 1;
                }
            }

            // After finishing the rank, flush trailing empties
            if empty > 0 {
                fen.push_str(&empty.to_string());
            }

            // Add '/' between ranks (but not after the last one)
            if rank > 0 {
                fen.push('/');
            }
        }
        return fen;
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

        return s;
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

    fn set_piece_at(&mut self, ch: char, idx: usize) -> Result<(), String> {
        let mask = 1u64 << idx;
        match ch {
            'P' => self.white_pawns |= mask,
            'N' => self.white_knights |= mask,
            'B' => self.white_bishops |= mask,
            'R' => self.white_rooks |= mask,
            'Q' => self.white_queens |= mask,
            'K' => self.white_king |= mask,
            'p' => self.black_pawns |= mask,
            'n' => self.black_knights |= mask,
            'b' => self.black_bishops |= mask,
            'r' => self.black_rooks |= mask,
            'q' => self.black_queens |= mask,
            'k' => self.black_king |= mask,
            _ => return Err(format!("Invalid piece char '{}'", ch)),
        }
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
        return Ok(());
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
