from engine.mailbox.board import Board
from engine.mailbox.zobrist import Zobrist
from engine.mailbox.moves.move import Move
from engine.mailbox.status import is_draw_by_repetition


# ────────────────────────────────────────────────────────────────
# Helper: build a minimal board for unit-tests
# ────────────────────────────────────────────────────────────────
def make_board(
    pieces: dict[tuple[int, int], str],
    *,
    disable_castling: bool = True,
    side_to_move: str = "white",
) -> Board:
    """
    Return a Board with the supplied *pieces* on an otherwise empty board.

    Parameters
    ----------
    pieces
        Mapping ``(file, rank) -> pieceChar`` using the single-letter
        representation from ``Board.PIECES`` (e.g. 'K', 'r', 'P', …).
    disable_castling
        When True (default) zeroes all castling flags so castling rights
        do *not* influence the repetition hash—ideal for king-shuffle tests.
    side_to_move
        'white' or 'black' to decide whose turn it is.
    """
    b = Board(Zobrist())

    # purge the board
    b.squares = [[b.EMPTY for _ in range(b.FILES)] for _ in range(b.RANKS)]
    for (f, r), p in pieces.items():
        b[(f, r)] = p

    b.side_to_move = side_to_move

    if disable_castling:
        b.white_can_castle_kingside = b.white_can_castle_queenside = False
        b.black_can_castle_kingside = b.black_can_castle_queenside = False

    b.zobrist_hash = b.zobrist.compute_hash(b, b.side_to_move)
    b.history = [b.zobrist_hash]
    return b


def play_moves(b: Board, moves: list[Move]) -> list[tuple]:
    """
    Play *moves* in order, returning the stack of (rights, halfmoveClock)
    tuples so that the caller can undo later.
    """
    rights_stack = []
    for mv in moves:
        rights_stack.append(b.make_move(mv))
    return rights_stack


# ────────────────────────────────────────────────────────────────
# Core tests from your original file
# ────────────────────────────────────────────────────────────────
def test_no_repetition_initially():
    b = make_board({(5, 1): "K", (5, 8): "k"})
    assert not is_draw_by_repetition(b)


def test_threefold_repetition_for_kings_back_and_forth():
    b = make_board({(5, 1): "K", (5, 8): "k"})
    cycle = [
        Move((5, 1), (5, 2)),
        Move((5, 8), (5, 7)),
        Move((5, 2), (5, 1)),
        Move((5, 7), (5, 8)),
    ]
    play_moves(b, cycle * 2)  # two cycles → 3 occurrences of start pos
    assert is_draw_by_repetition(b)


def test_twofold_not_threefold():
    b = make_board({(5, 1): "K", (5, 8): "k"})
    cycle = [
        Move((5, 1), (5, 2)),
        Move((5, 8), (5, 7)),
        Move((5, 2), (5, 1)),
        Move((5, 7), (5, 8)),
    ]
    play_moves(b, cycle)  # one cycle → 2 occurrences
    assert not is_draw_by_repetition(b)


def test_parameterised_counts():
    b = make_board({(5, 1): "K", (5, 8): "k"})
    cycle = [
        Move((5, 1), (5, 2)),
        Move((5, 8), (5, 7)),
        Move((5, 2), (5, 1)),
        Move((5, 7), (5, 8)),
    ]
    play_moves(b, cycle * 4)  # start + 4 cycles = 5 occurrences
    assert is_draw_by_repetition(b)  # default count=3
    assert is_draw_by_repetition(b, count=5)
    assert not is_draw_by_repetition(b, count=6)


def test_undo_restores_repetition_history():
    b = make_board({(5, 1): "K", (5, 8): "k"})
    cycle = [
        Move((5, 1), (5, 2)),
        Move((5, 8), (5, 7)),
        Move((5, 2), (5, 1)),
        Move((5, 7), (5, 8)),
    ]
    rights = play_moves(b, cycle * 2)  # two cycles → 3 occurrences
    assert is_draw_by_repetition(b)

    # Undo one ply: drop below threshold
    for mv in reversed(cycle[-1:]):
        b.undo_move(mv, *rights.pop())
    assert not is_draw_by_repetition(b)


# ────────────────────────────────────────────────────────────────
# New edge-case coverage
# ────────────────────────────────────────────────────────────────
def test_side_to_move_must_match():
    b = make_board({(5, 1): "K", (5, 8): "k"})
    b.make_move(Move((5, 1), (5, 2)))  # now Black to move, placement same
    assert not is_draw_by_repetition(b)


def test_castling_rights_difference_breaks_repetition():
    # keep castling rights ON for this test
    b = make_board(
        {(5, 1): "K", (5, 8): "k", (8, 1): "R"},
        disable_castling=False,
    )
    b.make_move(Move((8, 1), (8, 3)))  # rook leaves → rights gone
    b.make_move(Move((8, 3), (8, 1)))  # rook back, but rights differ
    assert not is_draw_by_repetition(b)


def test_en_passant_target_must_match():
    b = make_board(
        {(5, 1): "K", (5, 8): "k", (4, 2): "P", (3, 7): "p"},
    )
    b.make_move(Move((3, 7), (3, 5)))  # …c7-c5 sets ep square
    assert not is_draw_by_repetition(b)


def test_middle_position_repeats_three_times():
    b = make_board({(5, 1): "K", (4, 1): "R", (5, 8): "k"})
    cycle = [
        Move((4, 1), (4, 2)),
        Move((5, 8), (5, 7)),
        Move((4, 2), (4, 1)),
        Move((5, 7), (5, 8)),
    ]
    play_moves(b, cycle * 2)  # 1st repeat
    play_moves(b, cycle)  # 2nd repeat → 3 in total
    assert is_draw_by_repetition(b)


def test_capture_resets_practical_threefold():
    b = make_board({(5, 1): "K", (5, 8): "k", (4, 4): "R", (4, 7): "p"})
    b.make_move(Move((4, 4), (4, 7)))  # capture pawn
    shuffle = [
        Move((5, 1), (5, 2)),
        Move((5, 8), (5, 7)),
        Move((5, 2), (5, 1)),
        Move((5, 7), (5, 8)),
    ]
    play_moves(b, shuffle)  # ONE cycle → 2 occurrences
    assert not is_draw_by_repetition(b)


def test_fivefold_then_undo_to_threefold():
    b = make_board({(5, 1): "K", (5, 8): "k"})
    cycle = [
        Move((5, 1), (5, 2)),
        Move((5, 8), (5, 7)),
        Move((5, 2), (5, 1)),
        Move((5, 7), (5, 8)),
    ]
    rights = play_moves(b, cycle * 5)  # 6 occurrences (start+5 cycles)
    assert is_draw_by_repetition(b, count=5)

    # undo a full cycle (4 plies) → 5 occurrences remain
    for _ in range(4):
        mv = cycle.pop()
        b.undo_move(mv, *rights.pop())
    assert is_draw_by_repetition(b, count=5)
