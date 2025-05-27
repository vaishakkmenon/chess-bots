from engine.bitboard.constants import INITIAL_MASKS


class Board:
    def __init__(self):
        # a list of 12 ints, one per piece-type
        self.bitboards = [0] * 12
        self.init_positions()

    def init_positions(self):
        for idx in range(12):
            self.bitboards[idx] = INITIAL_MASKS[idx]
