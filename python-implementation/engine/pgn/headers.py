import re
from typing import List, Dict, Iterable

# Regex to allow [any_text + a space char + "words in quotes"]
TAG_PAIR_RE = re.compile(r'^\[([A-Za-z0-9_]+)\s+"(.*)"\]\s*$')


def parse_pgn_headers(lines: Iterable[str]) -> Dict[str, str]:
    tags: Dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line:
            break
        m = TAG_PAIR_RE.match(line)
        if m:
            tags[m.group(1)] = m.group(2)
        else:
            break
    return tags


def find_pgn_header_end(lines: List[str]) -> int:
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line or not TAG_PAIR_RE.match(line):
            return i
    return len(lines)
