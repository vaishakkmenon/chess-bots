import re
from typing import List, Dict
from collections import Counter
from engine.pgn.game import PGNGame  # noqa: TC002
from engine.bitboard.board import Board  # noqa: TC002
from engine.bitboard.config import RawMove  # noqa: TC002
from engine.bitboard.status import is_checkmate
from engine.bitboard.generator import generate_legal_moves
from engine.pgn.tokenizer import tokenize_movetext, TokenType
from engine.pgn.headers import parse_pgn_headers, find_pgn_header_end
from engine.bitboard.utils import algebraic_to_index, index_to_algebraic


class SanParsingError(Exception):
    pass


def find_ambiguities(board: Board, move: RawMove) -> List[int]:
    """
    Return a list of src-indices for every legal move of the same piece type
    that lands on move.dst (including move.src itself).
    """
    src, dst, _, _, _, _ = move
    piece_char = board.get_piece_char(src)
    piece_letter = piece_char.upper() if piece_char else ""
    ambiguous_srcs: List[int] = []
    for m in generate_legal_moves(board):
        m_src, m_dst, _, _, _, m_castle = m
        if m_castle or m_dst != dst:
            continue
        piece_char = board.get_piece_char(src)
        if piece_char is not None:
            if piece_char.upper() != piece_letter:
                continue
        ambiguous_srcs.append(m_src)
    return ambiguous_srcs


def choose_disambiguator(all_srcs: List[int], src: int) -> str:
    # No ambiguity if only one candidate
    if len(all_srcs) <= 1:
        return ""

    # Map each source to its file and rank
    files = [index_to_algebraic(s)[0] for s in all_srcs]
    ranks = [index_to_algebraic(s)[1] for s in all_srcs]
    file_counts = Counter(files)
    rank_counts = Counter(ranks)

    # Candidate’s file and rank
    my_file = index_to_algebraic(src)[0]
    my_rank = index_to_algebraic(src)[1]

    # 1) Unique file? use that
    if file_counts[my_file] == 1:
        return my_file

    # 2) Else unique rank? use that
    if rank_counts[my_rank] == 1:
        return my_rank

    # 3) Otherwise full square
    return index_to_algebraic(src)


def rawmove_to_san(board: Board, move: RawMove, *, check: bool = True) -> str:
    """
    Given a Board in its current position and a RawMove tuple,
    return the Standard Algebraic Notation string for that move.

    If `check=True`, append '+' or '#' when the move gives check or mate.
    """
    src, dst, is_capture, promotion, _, is_castle = move

    # Handle castling immediately
    if is_castle:
        return "O-O" if dst > src else "O-O-O"

    # Determine piece letter ("" for pawn, else uppercase)
    piece_char = board.get_piece_char(src)
    piece_letter = piece_char.upper() if piece_char else ""
    piece = "" if piece_letter == "P" else piece_letter
    dest = index_to_algebraic(dst)

    # === New: only compute a prefix if there's genuine ambiguity ===
    # Collect all source squares that could move the same piece to the same dst
    candidate_srcs: list[int] = []
    for m in generate_legal_moves(board):
        m_src, m_dst, *_ = m
        if m_dst != dst:
            continue
        pc = board.get_piece_char(m_src)
        if pc and pc.upper() == piece_letter:
            candidate_srcs.append(m_src)

    # If more than one such src exists, disambiguate; otherwise no prefix
    if len(candidate_srcs) <= 1:
        prefix = ""
    else:
        prefix = choose_disambiguator(candidate_srcs, src)

    # Build SAN: piece letter + (optional) prefix
    san = piece + prefix if piece else ""

    # Capture indicator
    if is_capture:
        if not piece:
            # pawn captures show file of departure
            san += index_to_algebraic(src)[0]
        san += "x"

    # Destination square
    san += dest

    # Promotion
    if promotion:
        san += "=" + promotion

    # Check/mate suffix
    if check:
        board.make_move_raw(move)
        try:
            if is_checkmate(board):
                san += "#"
            elif board.in_check(board.side_to_move):
                san += "+"
        finally:
            board.undo_move_raw()

    return san


def san_to_rawmove(board: Board, san: str) -> RawMove:
    clean = san.rstrip("+#")

    m = re.match(r"^([NBRQK]?)([a-h][1-8])$", clean)
    if m:
        piece_letter, dest_sq = m.groups()
        dest = algebraic_to_index(dest_sq)
        candidates: List[RawMove] = []
        for move in generate_legal_moves(board):
            src, dst, _, _, _, _ = move
            if dst != dest:
                continue
            pc = board.get_piece_char(src)
            if not pc:
                continue
            # if a letter was given, it must match
            if piece_letter and pc.upper() != piece_letter:
                continue
            # if no letter, must be a pawn move
            if not piece_letter and pc.upper() != "P":
                continue
            candidates.append(move)
        if len(candidates) == 1:
            return candidates[0]

    # 2) Fallback: round-trip via rawmove_to_san
    matches = [
        move
        for move in generate_legal_moves(board)
        if rawmove_to_san(board, move, check=False) == clean
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SanParsingError(f"No match for SAN “{san}”")
    raise SanParsingError(f"Ambiguous SAN “{san}”")


def read_pgn(text: str) -> PGNGame:
    """
    Parse the given PGN text (with one game) into a PGNGame:
      - tags: Dict[str,str]
      - moves: List[RawMove]
      - comments: Dict[int,str]   # ply index → comment text
      - nags:     Dict[int,List[int]]  # ply index → list of NAG codes
    """
    lines = text.splitlines()
    tags = parse_pgn_headers(lines)
    end_idx = find_pgn_header_end(lines)
    movetext_lines = lines[end_idx:]
    while movetext_lines and not movetext_lines[0].strip():
        movetext_lines.pop(0)

    movetext = " ".join(movetext_lines)
    tokens = tokenize_movetext(movetext)

    board = Board()
    moves: List[RawMove] = []
    comments: Dict[int, str] = {}
    nags: Dict[int, List[int]] = {}
    current_fullmove = 0

    for tok in tokens:
        if tok.type == TokenType.MOVE_NUMBER:
            # Extract fullmove number from "3." or "3..."
            num = int(tok.text.split(".")[0])
            current_fullmove = num

        elif tok.type == TokenType.SAN:
            rm = san_to_rawmove(board, tok.text)
            board.make_move_raw(rm)
            moves.append(rm)

        elif tok.type == TokenType.COMMENT:
            # Attach comment to this fullmove number
            comments[current_fullmove] = tok.text

        elif tok.type == TokenType.NAG:
            # Attach NAG(s) to this fullmove number
            nags.setdefault(current_fullmove, []).append(int(tok.text))

    return PGNGame(tags=tags, moves=moves, comments=comments, nags=nags)
