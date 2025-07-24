#[cfg(feature = "load-magic")]
pub fn load_magic_tables() -> MagicTables {
    const MAGIC_DATA: &[u8] = include_bytes!("../../../../data/magic_tables.bin");

    bincode::deserialize(MAGIC_DATA)
        .expect("Failed to deserialize magic_tables.bin (corrupt or outdated?)")
}
