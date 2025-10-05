use rand::RngCore;
use std::collections::HashMap;
use std::fs::OpenOptions;
use std::io::Write;

#[inline(always)]
// Generate a sparse 64-bit number by AND-ing three random values.
// This helps ensure a low number of set bits (sparse pattern),
// which reduces the chance of collisions in magic indexing.
pub fn random_sparse_u64<R: RngCore>(rng: &mut R) -> u64 {
    rng.next_u64() & rng.next_u64() & rng.next_u64()
}

pub fn is_magic_candidate_valid(blockers: &[u64], attacks: &[u64], magic: u64, shift: u32) -> bool {
    let mut seen: HashMap<u64, u64> = HashMap::new();

    for i in 0..blockers.len() {
        let blocker = blockers[i];
        let attack = attacks[i];
        let product = blocker.wrapping_mul(magic);
        let index = product >> shift;

        if let std::collections::hash_map::Entry::Vacant(e) = seen.entry(index) {
            e.insert(attack);
        } else {
            let existing_attack = seen[&index];
            if existing_attack != attack {
                return false;
            }
        }
    }

    true
}

pub fn find_magic_number_for_square<R: RngCore>(
    blockers: &[u64],
    attacks: &[u64],
    shift: u32,
    rng: &mut R,
) -> Result<u64, String> {
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

        let magic = random_sparse_u64(rng);

        if is_magic_candidate_valid(blockers, attacks, magic, shift) {
            writeln!(
                log_file,
                "Found magic number after {} attempts: {:#018x}",
                attempt + 1,
                magic
            )
            .expect("Failed to write to log file");
            return Ok(magic);
        }
    }

    writeln!(
        log_file,
        "Failed to find a valid magic number after 1,000,000 attempts"
    )
    .expect("Failed to write to log file");

    Err("Failed to find a valid magic number after 1,000,000 attempts".to_string())
}
