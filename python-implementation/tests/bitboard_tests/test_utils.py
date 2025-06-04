from engine.bitboard.utils import (
    pop_lsb,
    bit_count,
    lsb,
    msb,
    expand_occupancy,
)


def test_pop_lsb_nonzero():
    bb = 0b1011000  # bits at indices 3,4,6
    result = pop_lsb(bb)
    assert result == 3
    # ensure original bb is unchanged
    assert bb == 0b1011000


def test_pop_lsb_zero():
    assert pop_lsb(0) is None


def test_bit_count():
    assert bit_count(0b1011000) == 3
    assert bit_count(0) == 0
    assert bit_count(0xFFFF0000FFFF) == 32


def test_lsb():
    assert lsb(0b1000) == 3
    assert lsb(0) is None


def test_msb():
    assert msb(0b1011000) == 6
    assert msb(1 << 60) == 60
    assert msb(0) is None


def test_expand_occupancy_basic():
    mask = (1 << 1) | (1 << 4)
    assert expand_occupancy(0, mask) == 0
    assert expand_occupancy(1, mask) == (1 << 1)
    assert expand_occupancy(2, mask) == (1 << 4)
    assert expand_occupancy(3, mask) == mask


def test_expand_occupancy_larger_mask():
    mask = 0
    bits = [0, 3, 8, 12]
    for b in bits:
        mask |= 1 << b
    subset = 0b1010  # indices 1 and 3 -> squares bits[1]=3, bits[3]=12
    expected = (1 << bits[1]) | (1 << bits[3])
    assert expand_occupancy(subset, mask) == expected
