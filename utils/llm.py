"""
llm.py — Ollama LLM wrapper for ChillBot.

Provides a simple interface to query a locally running Ollama instance.
Supports both single-turn and multi-turn (chat) requests.
"""

import json
import logging
from typing import Optional

import requests

import config
from utils.logger import get_logger

import logging
logger = get_logger(__name__, level=logging.WARNING)

# Ollama REST endpoints
_GENERATE_URL = f"{config.OLLAMA_HOST}/api/generate"
_CHAT_URL = f"{config.OLLAMA_HOST}/api/chat"


def query_ollama(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> str:
    """
    Send a single prompt to Ollama and return the full response text.

    Args:
        prompt:      User prompt string.
        system:      Optional system message to prepend.
        model:       Model name override (defaults to config.OLLAMA_MODEL).
        temperature: Sampling temperature (lower = more deterministic).

    Returns:
        The model's response as a plain string.

    Raises:
        RuntimeError: If Ollama is unreachable or returns an error.
    """
    chosen_model = model or config.OLLAMA_MODEL

    payload: dict = {
        "model": chosen_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if system:
        payload["system"] = system

    logger.info("Querying Ollama model '%s'…", chosen_model)

    try:
        response = requests.post(
            _GENERATE_URL,
            json=payload,
            timeout=config.TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot connect to Ollama at {config.OLLAMA_HOST}. "
            "Is Ollama running? Try: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Ollama request timed out after {config.TIMEOUT}s. "
            "The model may be loading — please try again."
        )
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Ollama HTTP error: {exc}")
    except Exception as exc:
        raise RuntimeError(f"Unexpected Ollama error: {exc}")


def chat_ollama(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> str:
    """
    Send a multi-turn conversation to Ollama's /api/chat endpoint.

    Args:
        messages:    List of {"role": "user"|"assistant"|"system", "content": "…"}.
        model:       Model name override.
        temperature: Sampling temperature.

    Returns:
        The assistant's reply as a plain string.
    """
    chosen_model = model or config.OLLAMA_MODEL

    payload = {
        "model": chosen_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }

    logger.info("Chat request to Ollama model '%s' (%d messages)…", chosen_model, len(messages))

    try:
        response = requests.post(
            _CHAT_URL,
            json=payload,
            timeout=config.TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "").strip()

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot connect to Ollama at {config.OLLAMA_HOST}. "
            "Is Ollama running? Try: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Ollama request timed out after {config.TIMEOUT}s.")
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Ollama HTTP error: {exc}")
    except Exception as exc:
        raise RuntimeError(f"Unexpected Ollama error: {exc}")


def is_ollama_available() -> bool:
    """
    Check whether the Ollama server is reachable.

    Returns:
        True if Ollama responds, False otherwise.
    """
    try:
        response = requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
