"""
reflection.py — Post-reasoning reflection for ChillBot.

Reviews the final answer and only corrects it if it is clearly wrong.
Conservative by design — a good answer is never replaced.
"""

import logging

from utils.logger import get_logger
from utils.parser import parse_llm_json
from utils.prompts import REFLECTION_PROMPT

import logging
logger = get_logger(__name__, level=logging.WARNING)

# Minimum length for a corrected answer to be accepted.
# Prevents reflection from replacing a good answer with "{}" or "".
_MIN_CORRECTED_LENGTH = 20


def reflect(reasoning_chain: list[dict], final_answer: str) -> str:
    """
    Review the final answer and return it (possibly corrected).

    Args:
        reasoning_chain: List of ReAct step dicts.
        final_answer:    The formatted answer to review.

    Returns:
        The original answer, or a corrected one if reflection found real issues.
    """
    from utils.llm import query_ollama  # noqa: PLC0415

    if not final_answer or not final_answer.strip():
        return final_answer

    chain_text = _format_chain(reasoning_chain)

    # Escape braces in final_answer so .format() doesn't choke on them
    safe_answer = final_answer.replace("{", "{{").replace("}", "}}")

    prompt = REFLECTION_PROMPT.format(
        reasoning_chain=chain_text,
        final_answer=safe_answer,
    )

    logger.info("Running reflection on %d reasoning steps...", len(reasoning_chain))

    try:
        raw = query_ollama(prompt, temperature=0.0)
        result = parse_llm_json(raw)

        if result is None:
            logger.warning("Reflection returned unparseable output; keeping original.")
            return final_answer

        is_correct: bool = result.get("is_correct", True)
        issues: str = result.get("issues", "")
        corrected: str = result.get("corrected_answer", "")

        if is_correct:
            logger.info("Reflection: answer is correct.")
            return final_answer

        # Only accept the correction if it is substantive
        if corrected and len(corrected.strip()) >= _MIN_CORRECTED_LENGTH:
            logger.warning("Reflection found issues: %s", issues)
            return corrected.strip()
        else:
            logger.warning("Reflection correction too short/empty; keeping original.")
            return final_answer

    except Exception as exc:
        logger.error("Reflection failed: %s", exc)
        return final_answer


def _format_chain(chain: list[dict]) -> str:
    """Format the reasoning chain as readable text for the reflection prompt."""
    if not chain:
        return "(no reasoning steps)"
    parts = []
    for i, step in enumerate(chain, 1):
        parts.append(
            f"Step {i}: {step.get('action', '')} "
            f"-> {str(step.get('observation', ''))[:100]}"
        )
    return "\n".join(parts)
