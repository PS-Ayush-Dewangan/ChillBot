"""
fun_server.py — MCP Fun Server for ChillBot.

Provides lightweight fun tools backed by live APIs.
  • random_joke       — JokeAPI
  • motivation_quote  — Quotable API
"""

import io
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from mcp.server.fastmcp import FastMCP
from utils.helpers import http_get
from utils.logger import get_logger

logger = get_logger(__name__)

mcp = FastMCP("ChillBot Fun Server")


@mcp.tool()
def random_joke() -> str:
    """Fetch a random joke from JokeAPI."""
    data = http_get(
        "https://v2.jokeapi.dev/joke/Any",
        params={"blacklistFlags": "nsfw,racist,sexist,explicit", "type": "twopart,single"},
    )
    if not data or data.get("error"):
        return json.dumps({"error": "Could not fetch a joke right now. Try again!"})
    if data.get("type") == "twopart":
        return json.dumps({"setup": data["setup"], "punchline": data["delivery"]})
    return json.dumps({"joke": data["joke"]})


@mcp.tool()
def motivation_quote() -> str:
    """Fetch a motivational quote from the Quotable API."""
    data = http_get("https://api.quotable.io/random?tags=motivational|inspirational")
    if data and data.get("content"):
        return json.dumps({"content": data["content"], "author": data.get("author", "Unknown")})
    return json.dumps({"error": "Could not fetch a quote right now. Try again!"})


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    mcp.run(transport="stdio")
