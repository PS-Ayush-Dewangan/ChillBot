"""weather_server.py — Thin re-export. The get_weather tool lives in info_server.py."""
import io
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT.parent))

from servers.info_server import mcp, get_weather  # noqa: F401

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    mcp.run(transport="stdio")
