use rand::random;
use std::collections::HashMap;
use std::fs::OpenOptions;
use std::io::Write;

pub fn is_magic_candidate_valid(blockers: &[u64], attacks: &[u64], magic: u64, shift: u32) -> bool {
    let mut seen: HashMap<u64, u64> = HashMap::new();

    for i in 0..blockers.len() {
        let blocker = blockers[i];
        let attack = attacks[i];
        let product = blocker.wrapping_mul(magic);
        let index = product >> shift;

        if seen.contains_key(&index) {
            let existing_attack = seen[&index];
            if existing_attack != attack {
                return false;
            }
        } else {
            seen.insert(index, attack);
        }
    }

    return true;
}

pub fn find_magic_number_for_square(blockers: &[u64], attacks: &[u64], shift: u32) -> u64 {
    let mut log_file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("magic_search.log")
        .expect("Unable to open log file");

    for attempt in 0..1_000_000 {
        if attempt % 100_000 == 0 && attempt > 0 {
            writeln!(
                log_file,
                "Attempt {}... still searching for magic number",
                attempt
            )
            .expect("Failed to write to log file");
        }

        let magic = random::<u64>() & random::<u64>() & random::<u64>();

        if is_magic_candidate_valid(blockers, attacks, magic, shift) {
            writeln!(
                log_file,
                "Found magic number after {} attempts: {:#018x}",
                attempt + 1,
                magic
            )
            .expect("Failed to write to log file");
            return magic;
        }
    }

    writeln!(
        log_file,
        "Failed to find a valid magic number after 1,000,000 attempts"
    )
    .expect("Failed to write to log file");

    panic!("Failed to find a valid magic number after 1,000,000 attempts");
}
