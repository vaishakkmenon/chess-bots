import os
import subprocess
import sys
from pathlib import Path


def test_uci_smoke():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    proc = subprocess.Popen(
        [sys.executable, "-m", "engine.bitboard.uci"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    cmds = "uci\nisready\nposition startpos\ngo depth 1\nquit\n"
    out, _ = proc.communicate(cmds, timeout=5)
    assert "uciok" in out
    assert "readyok" in out
    assert "bestmove" in out
