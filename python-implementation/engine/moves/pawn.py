from board import Board
from .move import Move
from .helpers import check_bounds


def _generate_promotions(frm, to):
    """
    Yield the four promotion triples for a pawn move:
    (from_sq, to_sq, 'Q'), (from_sq, to_sq, 'R'), …
    """
    for piece in ("Q", "R", "B", "N"):
        yield Move(frm, to, piece)


def pawn_moves(board: Board, color: str) -> list[Move]:
    """Function to calculate all possible pawn moves
    Returns list of moves that include from, to, and promotion or not"""

    # Promotion Logic in function scope to keep pawn logic centralized
    def append_pawn_move(frm, to, promo_flag=None):
        """Helper to append either a normal move or the four promotions."""
        _, r2 = to
        if promo_flag is None and (
            r2 == Board.WHITE_PROMOTE_RANK or r2 == Board.BLACK_PROMOTE_RANK
        ):
            moves.extend(_generate_promotions(frm, to))
        else:
            moves.append(Move(frm, to, promo_flag))

    # list to store moves
    moves = []
    # Temporary storage of variables
    empty = Board.EMPTY

    # Set up variables that will be used later
    if color == "white":
        pawn_char = "P"
        move = 1
        start_rank = 2
        enemy_pieces = board.black_pieces
    else:
        pawn_char = "p"
        move = -1
        start_rank = 7
        enemy_pieces = board.white_pieces

    # Loops to go through the board and
    # perform checks on valid moves and captures

    for file in range(1, 9):
        for rank in range(1, 9):
            # Check if board position is a pawn
            if board[file, rank] == pawn_char:
                # Append single move forward
                first_target = newFile, newRank = file, rank + move

                on_board = check_bounds(newFile, newRank)
                is_empty = board[newFile, newRank] == empty

                if on_board and is_empty:
                    append_pawn_move((file, rank), first_target)

                # Append double move forward
                if rank == start_rank:
                    mid_f, mid_r = file, rank + move
                    double_move = end_f, end_r = file, rank + 2 * move
                    # Check if rank is valid
                    # Check one move and two moves is empty
                    if (
                        check_bounds(end_f, end_r)
                        and board[mid_f, mid_r] == empty
                        and board[end_f, end_r] == empty
                    ):
                        append_pawn_move((file, rank), double_move)

                # Calculate capture squares
                # Move is reused to calculate the rank
                #   the rank is only one off
                left_cap = leftFile, leftRank = file - 1, rank + move
                right_cap = rightFile, rightRank = file + 1, rank + move

                # Ensure you are capturing enemy piece and on the board
                if check_bounds(leftFile, leftRank) and board.holds(
                    (leftFile, leftRank), enemy_pieces
                ):
                    append_pawn_move((file, rank), left_cap)

                if check_bounds(rightFile, rightRank) and board.holds(
                    (rightFile, rightRank), enemy_pieces
                ):
                    append_pawn_move((file, rank), right_cap)

                # En-Passant Logic
                en_passant = board.en_passant_target
                if en_passant:
                    ep_file, ep_rank = en_passant
                    if ep_rank == rank + move and abs(ep_file - file) == 1:
                        moves.append(
                            Move(
                                (file, rank),
                                (ep_file, ep_rank),
                                is_en_passant=True,
                            )
                        )
    return moves
