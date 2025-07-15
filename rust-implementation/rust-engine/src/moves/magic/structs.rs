#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MagicEntry {
    pub magic: u64,
    pub shift: u32,
    pub table: Vec<u64>,
}

pub struct RookMagicTables {
    pub entries: [MagicEntry; 64],
}

pub struct BishopMagicTables {
    pub entries: [MagicEntry; 64],
}
