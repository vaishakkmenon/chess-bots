use rust_engine::board::{Board, Color};
use rust_engine::moves::execute::{generate_legal, make_move_basic};
use rust_engine::moves::magic::MagicTables;
use rust_engine::moves::magic::loader::load_magic_tables;
use rust_engine::moves::types::Move;
// use rust_engine::search::context::SearchContext;
// use rust_engine::search::opening_book::OpeningBook;
use rust_engine::search::search::minimax_basic;
// use rust_engine::search::tt::TranspositionTable;
use std::io::{self, BufRead};
use std::str::FromStr;
use std::time::Duration;

fn main() {
    // // Load opening book at startup
    // let book = OpeningBook::load("../books/Performance.bin")
    //     .map_err(|e| eprintln!("Warning: Could not load opening book: {}", e))
    //     .ok();

    // if book.is_some() {
    //     println!("info string Opening book loaded successfully");
    // }

    // Load magic tables once at startup
    let magic_tables = load_magic_tables();

    let mut board = Board::new(); // Start position
    // let mut tt = TranspositionTable::new(64); // 64 MB
    // let mut ctx = SearchContext::new();

    // Main UCI loop
    let stdin = io::stdin();
    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l.trim().to_string(),
            Err(_) => break,
        };

        if line.is_empty() {
            continue;
        }

        let parts: Vec<&str> = line.split_whitespace().collect();
        let command = parts[0];

        match command {
            "uci" => handle_uci(),
            "isready" => println!("readyok"),
            "ucinewgame" => {
                board = Board::new();
                // tt = TranspositionTable::new(64);
                // ctx = SearchContext::new();
            }
            "position" => {
                if let Some(new_board) = handle_position(&parts, &magic_tables) {
                    board = new_board;
                }
            }
            "go" => {
                handle_go(&parts, &mut board, &magic_tables);
            }
            "fen" => {
                println!("{}", board.to_fen());
            }
            "quit" => break,
            "d" | "display" => {
                println!("{}", board);
            }
            _ => {
                // Unknown command - UCI spec says to ignore
            }
        }
    }
}

fn handle_uci() {
    println!("id name Wayfinder 1.0 (Minimax)");
    println!("id author Vaishak Menon");
    println!("uciok");
}

fn handle_position(parts: &[&str], tables: &MagicTables) -> Option<Board> {
    let mut board = if parts.len() > 1 && parts[1] == "startpos" {
        Board::new()
    } else if parts.len() > 1 && parts[1] == "fen" {
        let fen_start = 2;
        let mut fen_end = parts.len();
        for (i, &part) in parts.iter().enumerate().skip(fen_start) {
            if part == "moves" {
                fen_end = i;
                break;
            }
        }

        let fen_string = parts[fen_start..fen_end].join(" ");
        Board::from_str(&fen_string).ok()?
    } else {
        Board::new()
    };

    // Apply moves if any
    if let Some(moves_idx) = parts.iter().position(|&p| p == "moves") {
        for move_str in &parts[moves_idx + 1..] {
            if let Some(mv) = parse_uci_move(&board, move_str, tables) {
                make_move_basic(&mut board, mv);
            } else {
                eprintln!("Invalid move: {}", move_str);
                return None;
            }
        }
    }

    Some(board)
}

fn parse_uci_move(board: &Board, move_str: &str, tables: &MagicTables) -> Option<Move> {
    if move_str.len() < 4 {
        return None;
    }

    // Parse UCI format: e2e4 or e7e8q
    let chars: Vec<char> = move_str.chars().collect();

    let from_file = (chars[0] as u8).wrapping_sub(b'a');
    let from_rank = (chars[1] as u8).wrapping_sub(b'1');
    let to_file = (chars[2] as u8).wrapping_sub(b'a');
    let to_rank = (chars[3] as u8).wrapping_sub(b'1');

    if from_file > 7 || from_rank > 7 || to_file > 7 || to_rank > 7 {
        return None;
    }

    let from_square = from_rank * 8 + from_file;
    let to_square = to_rank * 8 + to_file;

    // Get promotion piece if specified
    let promo_piece = if move_str.len() >= 5 {
        match chars[4] {
            'q' => Some(rust_engine::board::Piece::Queen),
            'r' => Some(rust_engine::board::Piece::Rook),
            'b' => Some(rust_engine::board::Piece::Bishop),
            'n' => Some(rust_engine::board::Piece::Knight),
            _ => None,
        }
    } else {
        None
    };

    // Generate legal moves and find match
    let mut moves = Vec::with_capacity(256);
    let mut scratch = Vec::with_capacity(256);

    let mut board_copy = board.clone();
    generate_legal(&mut board_copy, tables, &mut moves, &mut scratch);

    for mv in moves {
        if mv.from.index() == from_square && mv.to.index() == to_square {
            // Check promotion match
            if promo_piece.is_some() {
                if mv.promotion == promo_piece {
                    return Some(mv);
                }
            } else if mv.promotion.is_none() {
                return Some(mv);
            }
        }
    }

    None
}

fn handle_go(
    parts: &[&str],
    board: &mut Board,
    // tt: &mut TranspositionTable,
    // ctx: &mut SearchContext,
    tables: &MagicTables,
    // book: Option<&OpeningBook>,
) {
    let mut depth = 5;
    let mut time_limit = None;

    let mut i = 1;
    while i < parts.len() {
        match parts[i] {
            "depth" => {
                if i + 1 < parts.len() {
                    depth = parts[i + 1].parse().unwrap_or(6);
                }
                i += 2;
            }
            "movetime" => {
                if i + 1 < parts.len() {
                    let ms: u64 = parts[i + 1].parse().unwrap_or(5000);
                    time_limit = Some(Duration::from_millis(ms));
                }
                i += 2;
            }
            "wtime" => {
                if i + 1 < parts.len() {
                    let wtime: u64 = parts[i + 1].parse().unwrap_or(60000);
                    if board.side_to_move == Color::White {
                        // Allocate time for ~20 moves remaining
                        let moves_to_go = 20;
                        let time_for_move = wtime / moves_to_go;
                        time_limit = Some(Duration::from_millis(time_for_move));
                    }
                }
                i += 2;
            }
            "btime" => {
                if i + 1 < parts.len() {
                    let btime: u64 = parts[i + 1].parse().unwrap_or(60000);
                    if board.side_to_move == Color::Black {
                        let moves_to_go = 20;
                        let time_for_move = btime / moves_to_go;
                        time_limit = Some(Duration::from_millis(time_for_move));
                    }
                }
                i += 2;
            }
            "winc" => {
                if i + 1 < parts.len() {
                    let winc: u64 = parts[i + 1].parse().unwrap_or(0);
                    if board.side_to_move == Color::White {
                        if let Some(limit) = time_limit {
                            time_limit = Some(limit + Duration::from_millis(winc / 2));
                        }
                    }
                }
                i += 2;
            }
            "binc" => {
                if i + 1 < parts.len() {
                    let binc: u64 = parts[i + 1].parse().unwrap_or(0);
                    if board.side_to_move == Color::Black {
                        if let Some(limit) = time_limit {
                            time_limit = Some(limit + Duration::from_millis(binc / 2));
                        }
                    }
                }
                i += 2;
            }
            "movestogo" => {
                i += 2;
            }
            "infinite" => {
                depth = 100;
                time_limit = None;
                i += 1;
            }
            _ => {
                i += 1;
            }
        }
    }

    // tt.new_search();
    // ctx.clear_history();

    // Perform minimax search
    let (_score, best_move) = minimax_basic(board, tables, depth, true);
    // let (_score, best_move) = search_iterative_deepening(board, tables, depth);

    // Output best move
    if let Some(m) = best_move {
        println!("bestmove {}", m);
    } else {
        // No legal moves
        println!("bestmove 0000");
    }
}
