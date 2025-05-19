from board import Board
import moves

# 1) Start from the initial position
board = Board()
board.init_positions()
print(board)

# 2) Manually place a white pawn on e5
#    e5 is file=5, rank=5
board[(5, 5)] = "P"
#    Also clear whatever was on e2 and e4 to avoid confusion:
board[(5, 2)] = Board.EMPTY
board[(5, 4)] = Board.EMPTY
print("\nAfter placing pawn on e5:")
print(board)

# 3) Black double-push from d7 to d5
#    That should set en_passant_target to (4,6)
board.make_move((4, 7), (4, 5))
print("\nAfter d7→d5, EP target:", board.en_passant_target)
print(board)

# 4) Now generate white pawn moves—your code should include
#    the en passant capture from e5 → d6 (5,5→4,6)
white_moves = moves.pawn_moves(board, "white")
print("\nWhite moves now include en passant:", white_moves)
assert ((5, 5), (4, 6)) in white_moves
