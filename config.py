"""
config.py — Centralised configuration for ChillBot.

All settings are loaded from environment variables (via .env).
Import this module anywhere to access configuration values.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (works regardless of cwd)
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

# ---------------------------------------------------------------------------
# Ollama settings
# ---------------------------------------------------------------------------

OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral:7b")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# ---------------------------------------------------------------------------
# API keys (optional)
# ---------------------------------------------------------------------------

TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")

# ---------------------------------------------------------------------------
# Agent behaviour
# ---------------------------------------------------------------------------

# Maximum ReAct reasoning iterations before forcing a final answer
MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))

# HTTP request timeout in seconds
TIMEOUT: int = int(os.getenv("TIMEOUT", "15"))

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------

PREFERENCES_FILE: str = os.getenv("PREFERENCES_FILE", "preferences.json")
