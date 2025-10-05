# How to run tests in release mode

RUSTFLAGS="-C target-cpu=native -C target-feature=+popcnt,+lzcnt,+bmi2" \
cargo test --release --test perft_tests perft_startpos_depths -- --nocapture --test-threads=1