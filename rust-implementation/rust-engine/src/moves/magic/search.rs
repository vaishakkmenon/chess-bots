use rand::random;
use std::collections::HashMap;

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
    for attempt in 0..1_000_000 {
        let magic = random::<u64>() & random::<u64>() & random::<u64>();

        if is_magic_candidate_valid(blockers, attacks, magic, shift) {
            println!(
                "Found magic number after {} attempts: {:#018x}",
                attempt + 1,
                magic
            );
            return magic;
        }
    }

    panic!("Failed to find a valid magic number after 1,000,000 attempts");
}
