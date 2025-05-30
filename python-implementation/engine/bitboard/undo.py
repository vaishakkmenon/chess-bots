class Undo:
    def __init__(self, move, old_ep, captured_idx, cap_sq, prev_side):
        self.move = move
        self.old_ep = old_ep
        self.captured_idx = captured_idx
        self.cap_sq = cap_sq
        self.prev_side = prev_side
