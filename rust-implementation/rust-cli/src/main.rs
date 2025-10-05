use rust_engine::moves::magic::loader::load_magic_tables;

fn main() {
    let tables = load_magic_tables();

    println!("Rook magic table has {} entries", tables.rook.entries.len());
    println!(
        "Bishop magic table has {} entries",
        tables.bishop.entries.len()
    );

    // println!("\nFirst rook entry:\n{:#?}", tables.rook.entries[0]);
    // println!("\nFirst bishop entry:\n{:#?}", tables.bishop.entries[0]);
}
