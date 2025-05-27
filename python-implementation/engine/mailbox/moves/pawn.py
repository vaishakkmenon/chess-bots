from engine.mailbox.board import Board

from engine.mailbox.moves.move import Move
from engine.mailbox.moves.helpers import check_bounds

from typing import Optional


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
    def append_pawn_move(
        frm: tuple[int, int],
        to: tuple[int, int],
        promo_flag: Optional[str] = None,
    ):
        """Helper to append either a normal move or the four promotions."""
        _, r2 = to
        if promo_flag is None and r2 in (
            Board.WHITE_PROMOTE_RANK,
            Board.BLACK_PROMOTE_RANK,
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
        direction = 1
        start_rank = 2
        enemy_pieces = board.black_pieces
    else:
        pawn_char = "p"
        direction = -1
        start_rank = 7
        enemy_pieces = board.white_pieces

    # Loops to go through the board and
    # perform checks on valid moves and captures

    for file in range(1, 9):
        for rank in range(1, 9):
            # Check if board position is a pawn
            if board[file, rank] != pawn_char:
                continue
            # Append single move forward
            target_file, target_rank = file, rank + direction
            first_target = (target_file, target_rank)

            on_board = check_bounds(target_file, target_rank)
            is_empty = board[target_file, target_rank] == empty

            if on_board and is_empty:
                append_pawn_move((file, rank), first_target)

            # Append double move forward
            if rank == start_rank:
                mid_sq = (file, rank + direction)
                end_sq = (file, rank + 2 * direction)

                # Check if rank is valid
                # Check one move and two moves is empty
                if (
                    check_bounds(*end_sq)
                    and board[mid_sq] == empty
                    and board[end_sq] == empty
                ):
                    append_pawn_move((file, rank), end_sq)

            # Calculate capture squares
            # Move is reused to calculate the rank
            #   the rank is only one off
            left_file, left_rank = file - 1, rank + direction
            right_file, right_rank = file + 1, rank + direction

            left_sq = (left_file, left_rank)
            right_sq = (right_file, right_rank)

            # Ensure you are capturing enemy piece and on the board
            if check_bounds(left_file, left_rank) and board.holds(
                (left_file, left_rank), enemy_pieces
            ):
                append_pawn_move((file, rank), left_sq)

            if check_bounds(right_file, right_rank) and board.holds(
                (right_file, right_rank), enemy_pieces
            ):
                append_pawn_move((file, rank), right_sq)

            # En-Passant Logic
            en_passant = board.en_passant_target
            if en_passant:
                ep_file, ep_rank = en_passant
                if ep_rank == rank + direction and abs(ep_file - file) == 1:
                    moves.append(
                        Move(
                            (file, rank),
                            (ep_file, ep_rank),
                            is_en_passant=True,
                        )
                    )
    return moves
