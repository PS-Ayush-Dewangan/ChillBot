"""
parser.py — Robust JSON extraction and repair for ChillBot.

mistral:7b commonly produces these failure modes:
  1. JSON wrapped in ```json ... ``` fences
  2. Prose before/after the JSON object
  3. Truncated JSON (missing closing braces)
  4. Single-quoted keys instead of double-quoted
  5. Trailing commas
  6. The raw text IS the answer (no JSON at all)

This module tries every strategy before giving up.
"""

import json
import re
from typing import Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------

def _strip_fences(text: str) -> str:
    """Remove markdown code fences."""
    return re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()


def _fix_common_issues(text: str) -> str:
    """
    Apply lightweight fixes for common LLM JSON mistakes:
    - Trailing commas before } or ]
    - Single-quoted strings → double-quoted
    """
    # Remove trailing commas
    text = re.sub(r",\s*([}\]])", r"\1", text)
    # Single quotes → double quotes (simple cases only)
    text = re.sub(r"(?<![\\])'", '"', text)
    return text


def _find_json_object(text: str) -> Optional[str]:
    """
    Find the first complete {...} block using brace counting.
    More reliable than a greedy regex for nested objects.
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i, ch in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    # Brace never closed — return everything from start and hope for the best
    return text[start:]


def _try_parse(candidate: str) -> Optional[Any]:
    """Try json.loads, then with common fixes applied."""
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(_fix_common_issues(candidate))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Primary extraction — multiple strategies in order of confidence
# ---------------------------------------------------------------------------

def extract_json(text: str) -> Optional[Any]:
    """
    Extract a JSON object from raw LLM output using multiple strategies.

    Args:
        text: Raw string from the LLM.

    Returns:
        Parsed Python object, or None if all strategies fail.
    """
    if not text or not text.strip():
        return None

    cleaned = _strip_fences(text)

    # Strategy 1: parse the whole cleaned string directly
    result = _try_parse(cleaned)
    if result is not None:
        return result

    # Strategy 2: brace-counting to find the first complete {...}
    candidate = _find_json_object(cleaned)
    if candidate:
        result = _try_parse(candidate)
        if result is not None:
            return result

    # Strategy 3: greedy regex fallback (handles simple flat objects)
    match = re.search(r"\{[^{}]*\}", cleaned, re.DOTALL)
    if match:
        result = _try_parse(match.group(0))
        if result is not None:
            return result

    return None


# ---------------------------------------------------------------------------
# LLM-based repair
# ---------------------------------------------------------------------------

def repair_json_with_llm(broken_text: str) -> Optional[Any]:
    """
    Ask the LLM to fix malformed JSON and return the repaired object.

    Args:
        broken_text: The malformed JSON string.

    Returns:
        Parsed Python object, or None if repair also fails.
    """
    from utils.llm import query_ollama            # noqa: PLC0415
    from utils.prompts import JSON_REPAIR_PROMPT  # noqa: PLC0415

    prompt = JSON_REPAIR_PROMPT.format(broken_json=broken_text[:1000])
    logger.info("Attempting LLM JSON repair...")

    try:
        repaired = query_ollama(prompt, temperature=0.0)
        result = extract_json(repaired)
        if result is not None:
            logger.info("JSON repair succeeded.")
        else:
            logger.error("JSON repair failed — output still unparseable.")
        return result
    except Exception as exc:
        logger.error("JSON repair error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_llm_json(text: str) -> Optional[Any]:
    """
    Parse JSON from LLM output, falling back to LLM repair if needed.

    Args:
        text: Raw LLM response string.

    Returns:
        Parsed Python object, or None if all strategies fail.
    """
    result = extract_json(text)
    if result is not None:
        return result

    logger.info("Direct JSON extraction failed; invoking repair.")
    return repair_json_with_llm(text)
