from engine.bitboard.utils import pop_lsb, bit_count, lsb, msb


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
