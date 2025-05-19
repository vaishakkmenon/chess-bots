# File to store functions for generating moves
from board import Board


def pawn_moves(
    board: Board, color: str
) -> list[tuple[tuple[int, int], tuple[int, int]]]:

    # list to store moves
    moves = []
    # Temporary storage of variables
    empty = Board.EMPTY

    # Set up variables that will be used later
    if color == "white":
        pawn_char = "P"
        move = 1
        start_rank = 2
    else:
        pawn_char = "p"
        move = -1
        start_rank = 7

    """ Loops to go through the board and
    perform checks on valid moves and captures"""

    for file in range(1, 9):
        for rank in range(1, 9):
            # Check if board position is a pawn
            if board[file, rank] == pawn_char:
                # Append single move forward
                first_target = newFile, newRank = file, rank + move
                if 1 <= newRank <= 8 and board[newFile, newRank] == empty:
                    moves.append(((file, rank), first_target))

                # Append double move forward
                if rank == start_rank:
                    double_move = finalFile, finalRank = file, rank + move * 2
                    # Check if rank is valid
                    # Check one move and two moves is empty
                    if (
                        1 <= finalRank <= 8
                        and board[newFile, newRank] == empty
                        and board[finalFile, finalRank] == empty
                    ):
                        moves.append(((file, rank), double_move))

                # Calculate capture squares
                # Move is reused to calculate the rank
                #   the rank is only one off
                left_cap = leftFile, leftRank = file - 1, rank + move
                right_cap = rightFile, rightRank = file + 1, rank + move

                # Ensure files and ranks are within the board dimensions
                # Ensure the square has a piece to capture
                if (
                    1 <= leftFile <= 8
                    and 1 <= leftRank <= 8
                    and board[leftFile, leftRank] != empty
                    and board[leftFile, leftRank] != pawn_char
                ):
                    moves.append(((file, rank), left_cap))
                if (
                    1 <= rightFile <= 8
                    and 1 <= rightRank <= 8
                    and board[rightFile, rightRank] != empty
                    and board[rightFile, rightRank] != pawn_char
                ):
                    moves.append(((file, rank), right_cap))

                # En-Passant Logic
                en_passant = board.en_passant_target
                if en_passant:
                    ep_file, ep_rank = en_passant
                    if ep_rank == rank + move and abs(ep_file - file) == 1:
                        moves.append(((file, rank), (ep_file, ep_rank)))
    return moves
