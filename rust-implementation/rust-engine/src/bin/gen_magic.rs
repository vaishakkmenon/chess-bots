//! build_magic_tables.rs  (or whatever your binary target is)

use rust_engine::moves::magic::precompute::{MagicTableSeed, generate_magic_tables};
use std::{env, fs::File, io::Write};

//////////////////////////////////////////////////////////////////////////////
// 1)  Compile-time fallback seed  (only compiled when feature is ON)
//////////////////////////////////////////////////////////////////////////////
#[cfg(feature = "deterministic-magic")]
const FALLBACK_SEED: Option<u64> = Some(0x45); // 0x45 == 69₁₀

#[cfg(not(feature = "deterministic-magic"))]
const FALLBACK_SEED: Option<u64> = None; // default → random

//////////////////////////////////////////////////////////////////////////////
// 2)  Pick the seed for *this* run
//////////////////////////////////////////////////////////////////////////////
fn pick_seed() -> Option<u64> {
    // Highest priority: MAGIC_SEED env var
    if let Ok(s) = env::var("MAGIC_SEED") {
        if let Ok(n) = s.parse::<u64>() {
            return Some(n);
        }
        eprintln!("⚠️  MAGIC_SEED was set but isn't a valid u64: {s}");
    }
    // Otherwise, use the compile-time fallback (or None → random)
    FALLBACK_SEED
}

//////////////////////////////////////////////////////////////////////////////
// 3)  Main: build, serialise, write
//////////////////////////////////////////////////////////////////////////////
fn main() {
    // 3-a  Generate tables
    let seed_opt = pick_seed();
    let tables = match seed_opt {
        Some(seed) => generate_magic_tables(MagicTableSeed::Fixed(seed)),
        None => generate_magic_tables(MagicTableSeed::Randomized),
    }
    .expect("Failed to generate magic tables");

    // 3-b  Serialise with bincode
    let encoded = bincode::serialize(&tables).expect("Serialization failed");

    // 3-c  Persist to data/magic_tables.bin
    std::fs::create_dir_all("data").expect("Couldn't create data directory");
    let mut file = File::create("data/magic_tables.bin").expect("Couldn't create output file");
    file.write_all(&encoded).expect("Write failed!");

    match seed_opt {
        Some(s) => println!("✅  Tables saved (seed = {s}) → data/magic_tables.bin"),
        None => println!("✅  Tables saved (random seed) → data/magic_tables.bin"),
    }
}
