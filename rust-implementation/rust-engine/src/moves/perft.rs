use crate::board::Board;
use crate::moves::{
    execute::{generate_legal, make_move_basic, undo_move_basic},
    magic::MagicTables,
    square_control::in_check,
    types::Move,
};
use tracing::{debug, instrument, trace};

const MAX_LOG_DEPTH: u32 = 3; // only trace details for shallow nodes

pub struct PerftCounters {
    pub nodes: u64,
    pub captures: u64,
    pub ep_captures: u64,
    pub castles: u64,
    pub promotions: u64,
    pub checks: u64,
    pub checkmates: u64,
}

impl PerftCounters {
    pub fn zero() -> Self {
        Self {
            nodes: 0,
            captures: 0,
            ep_captures: 0,
            castles: 0,
            promotions: 0,
            checks: 0,
            checkmates: 0,
        }
    }
    pub fn add(&mut self, o: &PerftCounters) {
        self.nodes += o.nodes;
        self.captures += o.captures;
        self.ep_captures += o.ep_captures;
        self.castles += o.castles;
        self.promotions += o.promotions;
        self.checks += o.checks;
        self.checkmates += o.checkmates;
    }
}

#[inline]
fn sq_as_a1_zero(idx: u8) -> String {
    // Assumes 0 = a1, 63 = h8 (file = idx % 8, rank = idx / 8)
    let file = idx % 8;
    let rank = idx / 8;
    let f = (b'a' + file) as char;
    let r = (b'1' + rank) as char;
    format!("{f}{r}")
}

#[inline]
fn sq_as_a8_zero(idx: u8) -> String {
    // Assumes 0 = a8, 63 = h1 (file = idx % 8, rank = 7 - idx / 8)
    let file = idx % 8;
    let rank = 7 - (idx / 8);
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
    let mut scratch = Vec::with_capacity(256);
    generate_legal(board, tables, &mut moves, &mut scratch);

    let mut nodes = 0;
    for mv in moves {
        let undo = make_move_basic(board, mv);
        nodes += perft(board, tables, depth - 1);
        undo_move_basic(board, undo);
    }
    nodes
}

#[instrument(skip(board, tables), fields(depth))]
pub fn perft_divide(board: &mut Board, tables: &MagicTables, depth: u32) -> u64 {
    let mut moves = Vec::with_capacity(256);
    let mut scratch = Vec::with_capacity(256);
    generate_legal(board, tables, &mut moves, &mut scratch);

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

pub fn perft_count_with_breakdown(
    board: &mut Board,
    tables: &MagicTables,
    depth: u32,
    out: &mut PerftCounters,
) {
    if depth == 0 {
        out.nodes += 1;

        // Leaf: check/mate status (efficient: in_check + one legal gen)
        let side_in_check = in_check(board, board.side_to_move, tables);
        if side_in_check {
            out.checks += 1;
        }

        let mut tmp = Vec::new();
        let mut scratch = Vec::with_capacity(256);
        generate_legal(board, tables, &mut tmp, &mut scratch);
        if tmp.is_empty() && side_in_check {
            out.checkmates += 1;
        }
        return;
    }

    let mut moves = Vec::new();
    let mut scratch = Vec::with_capacity(256);
    generate_legal(board, tables, &mut moves, &mut scratch);

    for mv in moves {
        // --- breakdown tags at this ply (edge-based) ---
        if mv.is_capture {
            out.captures += 1;
            if mv.is_en_passant {
                out.ep_captures += 1;
            }
        }
        if mv.is_castling {
            out.castles += 1;
        }
        if mv.promotion.is_some() {
            out.promotions += 1;
        }

        #[cfg(debug_assertions)]
        let z0 = board.zobrist;

        let undo = make_move_basic(board, mv);
        perft_count_with_breakdown(board, tables, depth - 1, out);
        undo_move_basic(board, undo);

        #[cfg(debug_assertions)]
        {
            debug_assert_eq!(board.zobrist, z0, "zobrist changed across make/undo");
            debug_assert_eq!(
                board.compute_zobrist_full(),
                board.zobrist,
                "full recompute mismatch"
            );
        }
    }
}

pub fn perft_divide_with_breakdown(
    board: &mut Board,
    tables: &MagicTables,
    depth: u32,
) -> Vec<(Move, PerftCounters)> {
    let mut moves = Vec::with_capacity(256);
    let mut scratch = Vec::with_capacity(256);
    generate_legal(board, tables, &mut moves, &mut scratch);

    let mut out = Vec::with_capacity(moves.len());

    for mv in moves.iter().copied() {
        let undo = make_move_basic(board, mv);
        let mut pc = PerftCounters::zero();
        perft_count_with_breakdown(board, tables, depth - 1, &mut pc);
        undo_move_basic(board, undo);
        out.push((mv, pc));
    }
    out
}
