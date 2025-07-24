# Magic Table Data

This file was generated via `cargo run --bin gen_magic`.

It contains precomputed magic bitboards for rook and bishop sliding moves,
serialized with `bincode` for use with `include_bytes!()`.

If the generation code changes, re-run the generator and commit the new file.
