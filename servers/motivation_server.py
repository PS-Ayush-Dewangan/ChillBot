"""motivation_server.py — Thin re-export. The motivation_quote tool lives in fun_server.py."""
import io
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT.parent))

from servers.fun_server import mcp, motivation_quote  # noqa: F401

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    mcp.run(transport="stdio")
