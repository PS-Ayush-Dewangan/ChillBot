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


_FALLBACK_QUOTES = [
    {"content": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
    {"content": "It does not matter how slowly you go as long as you do not stop.", "author": "Confucius"},
    {"content": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
    {"content": "Start where you are. Use what you have. Do what you can.", "author": "Arthur Ashe"},
    {"content": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill"},
]


@mcp.tool()
def motivation_quote() -> str:
    """Fetch a motivational quote. Tries dummyjson → affirmations.dev → local fallback."""
    # Primary: dummyjson
    data = http_get("https://dummyjson.com/quotes/random")
    if data and data.get("quote"):
        return json.dumps({"content": data["quote"], "author": data.get("author", "Unknown")})

    # Secondary: affirmations.dev
    data2 = http_get("https://www.affirmations.dev/")
    if data2 and data2.get("affirmation"):
        return json.dumps({"content": data2["affirmation"], "author": "Daily Affirmation"})

    # Local fallback: never fails
    import random
    return json.dumps(random.choice(_FALLBACK_QUOTES))


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    mcp.run(transport="stdio")
