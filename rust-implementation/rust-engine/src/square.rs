use std::fmt;
use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Square(u8);

impl Square {
    pub fn from_index(idx: u8) -> Self {
        assert!(idx < 64, "Square index out of range");
        Square(idx)
    }

    pub fn index(self) -> u8 {
        self.0
    }
}

impl fmt::Display for Square {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let file = (self.0 % 8) as u8;
        let rank = (self.0 / 8) as u8;
        write!(f, "{}{}", (b'a' + file) as char, rank + 1)
    }
}

impl FromStr for Square {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let bytes = s.as_bytes();
        if bytes.len() != 2 {
            return Err(format!("Invalid square length: {}", s));
        }
        let mut file = bytes[0];
        let rank = bytes[1];

        if (b'A'..=b'H').contains(&file) {
            file = file + (b'a' - b'A');
        }

        if !(b'a'..=b'h').contains(&file) {
            return Err(format!("Invalid file: {}", s));
        }

        if !(b'1'..=b'8').contains(&rank) {
            return Err(format!("Invalid rank: {}", s));
        }

        let file_idx = file - b'a';
        let rank_idx = rank - b'1';
        Ok(Square(rank_idx * 8 + file_idx))
    }
}
