use crate::board::Board;
use crate::moves::{
    execute::{generate_legal, make_move_basic, undo_move_basic},
    magic::MagicTables,
};
use tracing::{debug, instrument, trace};

const MAX_LOG_DEPTH: u32 = 3; // only trace details for shallow nodes

#[inline]
fn sq_as_a1_zero(idx: u8) -> String {
    // Assumes 0 = a1, 63 = h8 (file = idx % 8, rank = idx / 8)
    let file = (idx % 8) as u8;
    let rank = (idx / 8) as u8;
    let f = (b'a' + file) as char;
    let r = (b'1' + rank) as char;
    format!("{f}{r}")
}

#[inline]
fn sq_as_a8_zero(idx: u8) -> String {
    // Assumes 0 = a8, 63 = h1 (file = idx % 8, rank = 7 - idx / 8)
    let file = (idx % 8) as u8;
    let rank = 7 - (idx / 8) as u8;
    let f = (b'a' + file) as char;
    let r = (b'1' + rank) as char;
    format!("{f}{r}")
}

#[instrument(skip(board, tables), fields(depth))]
pub fn perft(board: &mut Board, tables: &MagicTables, depth: u32) -> u64 {
    if depth == 0 {
        return 1;
    }

    let mut moves = Vec::new();
    generate_legal(board, tables, &mut moves);

    // helpful breadcrumb at each node
    if depth <= MAX_LOG_DEPTH {
        debug!(depth, moves = moves.len(), "perft: generated legal moves");
    }

    let mut nodes = 0;
    for mv in moves {
        if depth <= MAX_LOG_DEPTH {
            let from = mv.from.index(); // u8 or u16; cast to u8 if needed
            let to = mv.to.index();

            debug!(
                %mv,
                depth,
                from_idx = from,
                to_idx   = to,
                from_a1  = %sq_as_a1_zero(from as u8),
                to_a1    = %sq_as_a1_zero(to as u8),
                from_a8  = %sq_as_a8_zero(from as u8),
                to_a8    = %sq_as_a8_zero(to as u8),
                "perft: exploring move (decode check)"
            );
        }
        let undo = make_move_basic(board, mv);
        let child = perft(board, tables, depth - 1);
        nodes += child;
        undo_move_basic(board, undo);

        if depth <= MAX_LOG_DEPTH {
            trace!(%mv, depth, nodes = child, "perft: child result");
        }
    }

    if depth <= MAX_LOG_DEPTH {
        debug!(depth, total_nodes = nodes, "perft: return");
    }
    nodes
}

#[instrument(skip(board, tables), fields(depth))]
pub fn perft_divide(board: &mut Board, tables: &MagicTables, depth: u32) -> u64 {
    let mut moves = Vec::new();
    generate_legal(board, tables, &mut moves);

    if depth <= MAX_LOG_DEPTH {
        debug!(depth, moves = moves.len(), "divide: root legal moves");
    }

    let mut total = 0;
    for mv in moves {
        if depth <= MAX_LOG_DEPTH {
            // Replace `from()` / `to()` with your actual accessors if different.
            let from = mv.from.index();
            let to = mv.to.index();

            debug!(
                %mv, depth,
                from_idx = from, to_idx = to,
                from_a1 = %sq_as_a1_zero(from), to_a1 = %sq_as_a1_zero(to),
                from_a8 = %sq_as_a8_zero(from), to_a8 = %sq_as_a8_zero(to),
                "divide: exploring root move (decode check)"
            );
        }
        let undo = make_move_basic(board, mv);
        let count = perft(board, tables, depth - 1);
        undo_move_basic(board, undo);

        // --- INSERT #2: per-root child total (after recursion) ---
        if depth <= MAX_LOG_DEPTH {
            debug!(%mv, nodes = count, "divide: root child total");
        }
        // optional console
        println!("{}: {}", mv, count);
        total += count;
    }

    debug!(depth, total, "divide: total");
    println!("Total: {}", total);
    total
}
