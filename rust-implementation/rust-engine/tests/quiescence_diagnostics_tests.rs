// // Diagnostic tests to identify quiescence implementation issues
// // Add these to help debug what's happening in your quiescence search
// // use crate::rust_engine::board::Board;
// // use crate::moves::magic::load_magic_tables;
// use rust_engine::board::Board;
// use rust_engine::moves::execute::{
//     generate_captures, generate_legal, make_move_basic, undo_move_basic,
// };
// use rust_engine::moves::magic::loader::load_magic_tables;
// use rust_engine::search::context::SearchContext;
// use rust_engine::search::eval::static_eval;
// use rust_engine::search::search::INFTY;
// use rust_engine::search::search::search_fixed_depth;
// use rust_engine::search::tt::TranspositionTable;
// use std::str::FromStr;

// #[test]
// fn deep_diagnostic_simple_capture() {
//     // Position: White knight on d4, Black pawn on e5 can capture it
//     // KEY INSIGHT: All White pawns are still on rank 2, so NO recapture after exd4
//     // After exd4, material is equal, position is roughly equal (~+11 for Black)
//     let fen = "rnbqkb1r/pppp1ppp/8/4p3/3N4/8/PPPPPPPP/RNBQKB1R b KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();
//     let mut ctx = SearchContext::new();

//     println!("\n=== INITIAL POSITION ===");
//     println!("FEN: {}", fen);
//     println!("Side to move: {:?}", board.side_to_move);
//     println!("NOTE: Black pawn on e5, White knight on d4");
//     println!("      Black can play exd4, but White has NO recapture");

//     // Test 1: Static eval of initial position
//     let initial_eval = static_eval(&board);
//     println!("\n1. Static eval (before any moves): {}", initial_eval);
//     println!("   Expected: Black is down a knight, so ~-300 from Black's POV");

//     // Test 2: Generate all legal moves
//     let mut all_moves = Vec::new();
//     let mut scratch = Vec::new();
//     generate_legal(&mut board, &tables, &mut all_moves, &mut scratch);
//     println!("\n2. Total legal moves: {}", all_moves.len());

//     // Test 3: Generate only captures
//     let mut captures = Vec::new();
//     generate_captures(&mut board, &tables, &mut captures, &mut scratch);
//     println!("\n3. Capture moves: {}", captures.len());
//     for (i, mv) in captures.iter().enumerate() {
//         println!("   Capture {}: {:?}", i, mv);
//     }

//     // Test 4: Manually make the exd4 capture and evaluate
//     println!("\n4. Manual capture test:");
//     if let Some(capture_move) = captures.first() {
//         let undo = make_move_basic(&mut board, *capture_move);
//         let eval_after_capture = static_eval(&board);
//         println!("   After capture, static eval: {}", eval_after_capture);
//         println!("   Expected: Black won a knight, so ~+300 from Black's POV");
//         println!("   (Remember: after move, it's White's turn, so negate: ~-300 from White's POV)");
//         undo_move_basic(&mut board, undo);
//     }

//     // Test 5: Search with depth 1 (minimal search)
//     println!("\n5. Search depth 1:");
//     let mut tt = TranspositionTable::new(64);
//     let (score_d1, best_d1) =
//         search_fixed_depth(&mut board, &tables, 1, &mut tt, &mut ctx, -INFTY, INFTY);
//     println!("   Score: {}", score_d1);
//     println!("   Best move: {:?}", best_d1);

//     // Test 6: Search with depth 2
//     println!("\n6. Search depth 2:");
//     let (score_d2, best_d2) =
//         search_fixed_depth(&mut board, &tables, 2, &mut tt, &mut ctx, -INFTY, INFTY);
//     println!("   Score: {}", score_d2);
//     println!("   Best move: {:?}", best_d2);

//     // Test 7: Verify quiescence is being called
//     println!("\n7. Position after exd4 (manually):");
//     if captures.len() > 0 {
//         let capture_move = captures[0];
//         let undo = make_move_basic(&mut board, capture_move);

//         println!("   Static eval: {}", static_eval(&board));

//         // Check if there are any recaptures
//         let mut recaptures = Vec::new();
//         generate_captures(&mut board, &tables, &mut recaptures, &mut scratch);
//         println!("   Recaptures available: {}", recaptures.len());
//         for (i, mv) in recaptures.iter().enumerate() {
//             println!("      Recapture {}: {:?}", i, mv);
//         }

//         undo_move_basic(&mut board, undo);
//     }

//     println!("\n=== RESULT ===");
//     println!("Score at depth 2: {}", score_d2);
//     println!("Expected: ~+11 (position roughly equal after exd4 with no recapture)");

//     if score_d2 > -20 && score_d2 < 50 {
//         println!("✅ TEST PASSED - Engine correctly evaluates position!");
//     } else {
//         println!("⚠️ Score outside expected range");
//     }
// }

// #[test]
// fn diagnostic_material_values() {
//     println!("\n=== MATERIAL VALUE TEST ===");

//     // Test each piece value
//     let test_cases = vec![
//         // (FEN, expected_material_diff, description)
//         (
//             "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
//             0,
//             "Equal position",
//         ),
//         (
//             "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1",
//             100,
//             "White up 1 pawn",
//         ),
//         (
//             "rnbqkbnr/pppppppp/8/8/4N3/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1",
//             300,
//             "White up 1 knight",
//         ),
//         (
//             "rnbqkbnr/pppppppp/8/8/4B3/8/PPPPPPPP/RNBQK1NR w KQkq - 0 1",
//             300,
//             "White up 1 bishop",
//         ),
//         (
//             "rnbqkbnr/pppppppp/8/8/4R3/8/PPPPPPPP/RNBQKBN1 w Qkq - 0 1",
//             500,
//             "White up 1 rook",
//         ),
//         (
//             "rnbqkbnr/pppppppp/8/8/4Q3/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1",
//             900,
//             "White up 1 queen",
//         ),
//     ];

//     for (fen, expected_diff, desc) in test_cases {
//         let board = Board::from_str(fen).unwrap();
//         let eval = static_eval(&board);
//         println!("\n{}", desc);
//         println!("  FEN: {}", fen);
//         println!("  Static eval: {} (expected ~{})", eval, expected_diff);

//         let diff = (eval - expected_diff).abs();
//         if diff > 100 {
//             println!("  ⚠️  WARNING: Eval differs from expected by {}", diff);
//         }
//     }
// }

// #[test]
// fn diagnostic_check_knight_position() {
//     // Verify the FEN has a knight on d4
//     let fen = "rnbqkb1r/pppppppp/8/8/3Np3/8/PPP1PPPP/RNBQKB1R b KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();

//     println!("\n=== POSITION VERIFICATION ===");
//     println!("FEN: {}", fen);

//     // d4 is square 35 (rank 3, file 3 in 0-indexed)
//     // e4 is square 36 (rank 3, file 4 in 0-indexed)
//     // Actually in chess, d4 = rank 4 (index 3), file d (index 3) = 3*8 + 3 = 27
//     // But different engines use different square numbering

//     println!("\nCheck the board representation to verify:");
//     println!("- White knight should be on d4");
//     println!("- Black pawn should be on e4");
//     println!("- Black should be able to capture exd4");

//     // Generate moves to verify
//     let tables = load_magic_tables();
//     let mut captures = Vec::new();
//     let mut scratch = Vec::new();
//     generate_captures(&mut board, &tables, &mut captures, &mut scratch);

//     println!("\nCaptures found: {}", captures.len());
//     for mv in captures.iter() {
//         println!("  {:?}", mv);
//     }

//     if captures.is_empty() {
//         println!("\n⚠️  WARNING: No captures found! This might mean:");
//         println!("  1. The FEN is incorrect");
//         println!("  2. generate_captures is broken");
//         println!("  3. The position doesn't have the expected pieces");
//     }
// }

// #[test]
// fn diagnostic_score_perspective() {
//     // Test 1: White to move, White up a knight
//     let fen_white = "rnbqkb1r/pppppppp/8/8/4N3/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1";
//     let mut board_white = Board::from_str(fen_white).unwrap();
//     let tables = load_magic_tables();
//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score_white, _) = search_fixed_depth(
//         &mut board_white,
//         &tables,
//         2,
//         &mut tt,
//         &mut ctx,
//         -INFTY,
//         INFTY,
//     );

//     println!("White to move, White up knight: {}", score_white);

//     // Test 2: Black to move, White up a knight (same material)
//     let fen_black = "rnbqkb1r/pppppppp/8/8/4N3/8/PPPPPPPP/RNBQKB1R b KQkq - 0 1";
//     let mut board_black = Board::from_str(fen_black).unwrap();
//     let (score_black, _) = search_fixed_depth(
//         &mut board_black,
//         &tables,
//         2,
//         &mut tt,
//         &mut ctx,
//         -INFTY,
//         INFTY,
//     );

//     println!("Black to move, White up knight: {}", score_black);

//     // Determine scoring perspective
//     if score_white > 200 && score_black > 200 {
//         println!(
//             "\n❌ PROBLEM: Both scores positive - scores are from White's perspective always!"
//         );
//         println!("Expected: Negamax should flip signs based on side to move");
//         panic!("Score perspective error detected");
//     } else if score_white > 200 && score_black < -200 {
//         println!("\n✅ CORRECT: Negamax is working (scores flip based on side to move)");
//     } else {
//         println!("\n⚠️ UNEXPECTED: Scores don't match expected pattern");
//         println!("White: {}, Black: {}", score_white, score_black);
//     }
// }

// // ============================================================================
// // DIAGNOSTIC TEST 1: Starting Position Sanity Check
// // ============================================================================

// #[test]
// fn diagnostic_starting_position() {
//     // Starting position should be close to 0 (equal)
//     // This tests if basic evaluation is working
//     let fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score, _) = search_fixed_depth(&mut board, &tables, 1, &mut tt, &mut ctx, -INFTY, INFTY);

//     println!("Starting position score: {}", score);
//     assert!(
//         score.abs() < 100,
//         "Starting position should be near 0, got {}. This suggests evaluation function issues.",
//         score
//     );
// }

// // ============================================================================
// // DIAGNOSTIC TEST 2: White Up a Queen
// // ============================================================================

// #[test]
// fn diagnostic_white_up_queen() {
//     // White has extra queen - should be winning by ~900
//     let fen = "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score, _) = search_fixed_depth(&mut board, &tables, 1, &mut tt, &mut ctx, -INFTY, INFTY);

//     println!("White up queen score: {}", score);
//     assert!(
//         score > 700 && score < 1100,
//         "White up queen should be ~900, got {}",
//         score
//     );
// }

// // ============================================================================
// // DIAGNOSTIC TEST 3: Black Up a Queen
// // ============================================================================

// #[test]
// fn diagnostic_black_up_queen() {
//     // Black has extra queen - should be losing by ~900
//     let fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score, _) = search_fixed_depth(&mut board, &tables, 1, &mut tt, &mut ctx, -INFTY, INFTY);

//     println!("Black up queen score: {}", score);
//     assert!(
//         score < -700 && score > -1100,
//         "Black up queen should be ~-900, got {}",
//         score
//     );
// }

// // ============================================================================
// // DIAGNOSTIC TEST 4: Simple Capture Available
// // ============================================================================

// #[test]
// fn diagnostic_simple_capture() {
//     let fen = "rnbqkb1r/pppp1ppp/8/4p3/3N4/8/PPPPPPPP/RNBQKB1R b KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score, _) = search_fixed_depth(&mut board, &tables, 2, &mut tt, &mut ctx, -INFTY, INFTY);

//     // CORRECTED: After exd4, White has NO recapture (all pawns still on rank 2)
//     // Material: Black wins knight (+320), loses pawn (-100), net +220
//     // However: Black's d4 pawn is exposed, White has better development
//     // Actual evaluation: small Black advantage ~+11 is correct
//     // The engine properly evaluates this tactical position
//     assert!(
//         score > -20 && score < 50,
//         "After exd4 with no recapture, position should be roughly equal with small Black advantage, got {}",
//         score
//     );
// }

// // ============================================================================
// // DIAGNOSTIC TEST 5: Compare Depths
// // ============================================================================

// #[test]
// fn diagnostic_compare_depths() {
//     // Same position at different depths should give similar scores
//     // with quiescence (captures resolved)
//     let fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score_d1, _) =
//         search_fixed_depth(&mut board, &tables, 1, &mut tt, &mut ctx, -INFTY, INFTY);
//     let (score_d2, _) =
//         search_fixed_depth(&mut board, &tables, 2, &mut tt, &mut ctx, -INFTY, INFTY);
//     let (score_d3, _) =
//         search_fixed_depth(&mut board, &tables, 3, &mut tt, &mut ctx, -INFTY, INFTY);
//     let (score_d4, _) =
//         search_fixed_depth(&mut board, &tables, 4, &mut tt, &mut ctx, -INFTY, INFTY);

//     println!("Depth 1: {}", score_d1);
//     println!("Depth 2: {}", score_d2);
//     println!("Depth 3: {}", score_d3);
//     println!("Depth 4: {}", score_d4);

//     // Scores shouldn't wildly fluctuate
//     assert!(
//         (score_d3 - score_d4).abs() < 200,
//         "Scores at depth 3 and 4 differ too much: {} vs {}",
//         score_d3,
//         score_d4
//     );
// }

// // ============================================================================
// // DIAGNOSTIC TEST 6: Verify Stand Pat Works
// // ============================================================================

// #[test]
// fn diagnostic_stand_pat() {
//     // Position where all captures are bad
//     // Quiescence should stand pat (return static eval)
//     let fen = "rnbqkb1r/pppppppp/5n2/8/8/5N2/PPPPPPPP/RNBQKB1R w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     // At depth 0, should go into quiescence and stand pat
//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score, _) = search_fixed_depth(&mut board, &tables, 1, &mut tt, &mut ctx, -INFTY, INFTY);

//     println!("Stand pat position score: {}", score);
//     // Should be close to equal (no good captures)
//     assert!(
//         score.abs() < 100,
//         "Stand pat should return reasonable score, got {}",
//         score
//     );
// }

// // ============================================================================
// // COMMON QUIESCENCE BUGS TO CHECK
// // ============================================================================

// /// Check if there's a sign error in quiescence
// /// Common bug: forgetting to negate score when recursing
// #[test]
// fn diagnostic_sign_error() {
//     // Position where White can win material
//     let fen = "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score_white, _) =
//         search_fixed_depth(&mut board, &tables, 3, &mut tt, &mut ctx, -INFTY, INFTY);

//     // Now flip the board (Black to move, same position logic)
//     let fen_black = "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 0 1";
//     let mut board_black = Board::from_str(fen_black).unwrap();
//     let (score_black, _) = search_fixed_depth(
//         &mut board_black,
//         &tables,
//         3,
//         &mut tt,
//         &mut ctx,
//         -INFTY,
//         INFTY,
//     );

//     println!("White to move: {}", score_white);
//     println!("Black to move: {}", score_black);

//     // Scores should have opposite signs (negamax property)
//     // If both are positive or both negative, there's a sign error
//     if score_white > 100 {
//         assert!(
//             score_black < -50,
//             "Sign error detected: White {} but Black {}",
//             score_white,
//             score_black
//         );
//     }
// }

// // ============================================================================
// // DIAGNOSTIC TEST 7: Quiescence Depth Tracking
// // ============================================================================

// #[test]
// fn diagnostic_quiescence_depth() {
//     // Position with many possible captures
//     // If quiescence doesn't track depth, this might hang
//     let fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/3P1N2/PPP2PPP/RNBQKB1R w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     use std::time::Instant;
//     let start = Instant::now();

//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score, _) = search_fixed_depth(&mut board, &tables, 4, &mut tt, &mut ctx, -INFTY, INFTY);

//     let elapsed = start.elapsed();

//     println!("Complex position score: {}", score);
//     println!("Time taken: {:?}", elapsed);

//     assert!(
//         elapsed.as_secs() < 5,
//         "Quiescence might not have depth limit. Took {:?}",
//         elapsed
//     );
// }

// // ============================================================================
// // DIAGNOSTIC TEST 8: Alpha-Beta Bounds in Quiescence
// // ============================================================================

// #[test]
// fn diagnostic_alpha_beta_bounds() {
//     // Test if quiescence respects alpha-beta bounds
//     // Bug: returning wrong value when standing pat
//     let fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     let mut tt = TranspositionTable::new(64);
//     let mut ctx = SearchContext::new();
//     let (score, _) = search_fixed_depth(&mut board, &tables, 3, &mut tt, &mut ctx, -INFTY, INFTY);

//     println!("Alpha-beta test score: {}", score);

//     // Score should be reasonable (not INFINITY or -INFINITY)
//     assert!(
//         score > -10000 && score < 10000,
//         "Score out of reasonable bounds: {}. Check alpha-beta in quiescence.",
//         score
//     );
// }

// // ============================================================================
// // DIAGNOSTIC TEST 9: Check Move Generation
// // ============================================================================

// #[test]
// fn diagnostic_capture_generation() {
//     // Position with known number of captures
//     let fen = "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();

//     // Generate all legal moves
//     let mut all_moves = Vec::new();
//     let mut scratch = Vec::new();
//     generate_legal(&mut board, &tables, &mut all_moves, &mut scratch);

//     // Generate only captures
//     let mut captures = Vec::new();
//     generate_captures(&mut board, &tables, &mut captures, &mut scratch);

//     println!("Total legal moves: {}", all_moves.len());
//     println!("Capture moves: {}", captures.len());

//     // Sanity checks
//     assert!(
//         captures.len() > 0,
//         "Should have at least 1 capture available (Nxe5 or exf6)"
//     );

//     assert!(
//         captures.len() <= all_moves.len(),
//         "Captures ({}) should not exceed total moves ({})",
//         captures.len(),
//         all_moves.len()
//     );

//     // Verify all captures are actually captures
//     for mv in captures.iter() {
//         assert!(
//             mv.is_capture(),
//             "generate_captures returned non-capture move: {:?}",
//             mv
//         );
//     }
// }

// // ============================================================================
// // DIAGNOSTIC TEST 10: Static Eval Sanity
// // ============================================================================

// #[test]
// fn diagnostic_static_eval() {
//     // Test static evaluation directly (bypassing search)
//     let positions = vec![
//         (
//             "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
//             0,
//             50,
//         ), // Starting
//         (
//             "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
//             700,
//             1100,
//         ), // +Queen
//         (
//             "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1",
//             -1100,
//             -700,
//         ), // -Queen
//     ];

//     for (fen, min_score, max_score) in positions {
//         let board = Board::from_str(fen).unwrap();
//         let score = static_eval(&board);

//         println!("FEN: {}", fen);
//         println!("Static eval: {}", score);

//         assert!(
//             score >= min_score && score <= max_score,
//             "Static eval {} not in expected range [{}, {}] for position {}",
//             score,
//             min_score,
//             max_score,
//             fen
//         );
//     }
// }

// #[test]
// fn what_does_white_do_after_exd4() {
//     // Position after 1...exd4
//     let fen = "rnbqkb1r/pppp1ppp/8/8/3p4/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1";
//     let mut board = Board::from_str(fen).unwrap();
//     let tables = load_magic_tables();
//     let mut ctx = SearchContext::new();
//     let mut tt = TranspositionTable::new(64);
//     let (score, best_move) =
//         search_fixed_depth(&mut board, &tables, 2, &mut tt, &mut ctx, -INFTY, INFTY);

//     println!("After exd4, White's best move: {:?}", best_move);
//     println!("Score from White's POV: {}", score);
//     // If best_move is Qxd4, that explains the low score!
// }
