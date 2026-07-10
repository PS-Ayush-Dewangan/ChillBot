"""
helpers.py — Shared utility functions for ChillBot.

Covers HTTP requests with retry/timeout, JSON file I/O,
and user preferences management.
"""

import json
import time
from pathlib import Path
from typing import Any, Optional

import requests

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT = 10   # seconds
_MAX_RETRIES = 3
_RETRY_DELAY = 1.5      # seconds between retries


def http_get(url: str, params: Optional[dict] = None, timeout: int = _DEFAULT_TIMEOUT) -> Optional[dict]:
    """
    Perform a GET request with automatic retry and timeout handling.

    Args:
        url:     Target URL.
        params:  Optional query parameters.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response dict, or None on failure.
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning("Request timed out (attempt %d/%d): %s", attempt, _MAX_RETRIES, url)
        except requests.exceptions.HTTPError as exc:
            logger.warning("HTTP error %s for %s", exc.response.status_code, url)
            return None  # Don't retry on HTTP errors (4xx/5xx)
        except requests.exceptions.ConnectionError:
            logger.warning("Connection error (attempt %d/%d): %s", attempt, _MAX_RETRIES, url)
        except Exception as exc:
            logger.error("Unexpected error fetching %s: %s", url, exc)
            return None

        if attempt < _MAX_RETRIES:
            time.sleep(_RETRY_DELAY)

    logger.error("All %d attempts failed for: %s", _MAX_RETRIES, url)
    return None


# ---------------------------------------------------------------------------
# JSON file helpers
# ---------------------------------------------------------------------------

def load_json_file(path: str | Path) -> Any:
    """
    Load and return the contents of a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON content (list or dict), or None on failure.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        logger.error("JSON file not found: %s", path)
        return None
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", path, exc)
        return None


def save_json_file(path: str | Path, data: Any) -> bool:
    """
    Persist data to a JSON file (pretty-printed).

    Args:
        path: Destination file path.
        data: Serialisable Python object.

    Returns:
        True on success, False on failure.
    """
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        return True
    except Exception as exc:
        logger.error("Failed to write JSON to %s: %s", path, exc)
        return False


# ---------------------------------------------------------------------------
# Preferences helpers
# ---------------------------------------------------------------------------

def load_preferences(path: str | Path = "preferences.json") -> dict:
    """Load user preferences, returning an empty dict if unavailable."""
    data = load_json_file(path)
    return data if isinstance(data, dict) else {}


def save_preferences(prefs: dict, path: str | Path = "preferences.json") -> bool:
    """Persist updated user preferences."""
    return save_json_file(path, prefs)


def update_preference(key: str, value: Any, path: str | Path = "preferences.json") -> None:
    """
    Update a single preference key and persist immediately.

    Args:
        key:   Preference key (e.g. 'favourite_genre').
        value: New value.
        path:  Path to preferences file.
    """
    prefs = load_preferences(path)
    prefs[key] = value
    save_preferences(prefs, path)
    logger.info("Preference updated: %s = %s", key, value)
