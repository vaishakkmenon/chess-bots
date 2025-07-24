use rust_engine::moves::magic::precompute::generate_magic_tables;
use std::fs::File;
use std::io::Write;

fn main() {
    let tables = match generate_magic_tables() {
        Ok(t) => t,
        Err(e) => {
            eprintln!("Failed to generate magic tables: {e}");
            std::process::exit(1);
        }
    };

    let encoded = bincode::serialize(&tables).expect("Serialization failed");
    std::fs::create_dir_all("data").expect("Couldn't create data directory");
    let mut file = File::create("data/magic_tables.bin").expect("Couldn't create output file");

    file.write_all(&encoded).expect("Write failed!");
    println!("Magic tables saved to data/magic_tables.bin");
}
