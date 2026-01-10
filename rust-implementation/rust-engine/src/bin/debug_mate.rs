fn main() {
    use rust_engine::board::{Board, Color, Piece};
    use rust_engine::moves::execute::generate_legal;
    use rust_engine::moves::magic::loader::load_magic_tables;

    println!("Loading magic tables...");
    let tables = load_magic_tables();

    // Setup: Hanging Queen FEN
    // FEN: "rnbqkbnr/pppp1ppp/8/4Q3/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 0 1"
    let fen = "rnbqkbnr/pppp1ppp/8/4Q3/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 0 1";
    let mut board = Board::new();
    board.set_fen(fen).unwrap();
    println!("FEN: {}", board.to_fen());
    println!("Occupied: {:#066b}", board.occupied());
    println!(
        "White Queen: {:#066b}",
        board.pieces(Piece::Queen, Color::White)
    );
    println!(
        "Black Queen: {:#066b}",
        board.pieces(Piece::Queen, Color::Black)
    );

    let mut moves = Vec::new();
    let mut scratch = Vec::new();
    generate_legal(&mut board, &tables, &mut moves, &mut scratch);

    println!("Generated {} legal moves for Black:", moves.len());
    let mut found_capture = false;
    for mv in moves {
        println!("  {}", mv.to_uci());
        if mv.to_uci() == "d8e5" { // No, UCI for capture is from-to not piece
            // "d8e5"
        }
        if mv.from.index() == 59 && mv.to.index() == 36 {
            // d8 (59) -> e5 (36)?
            // d8=59. e5?
            // e5: rank 4 (0-based) * 8 + file 4 = 32+4 = 36. Correct.
            println!("CRITICAL: Found Queen Capture: {}", mv.to_uci());
            found_capture = true;
        }
    }

    if found_capture {
        println!("PASS: Queen capture generated.");
    } else {
        println!("FAIL: Queen capture missed.");
    }
}
