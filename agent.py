"""
agent.py — ChillBot AI Agent (ReAct loop).

Flow per turn:
  1. LLM decides: call a tool OR answer directly (FINISH).
  2. If tool called → raw result fed back to LLM → LLM writes human answer.
  3. Reflection verifies the answer.
"""

import asyncio
import json
import logging
import re
import sys
from pathlib import Path

import config
from utils.cli import (
    console,
    print_banner,
    print_server_status,
    print_thought,
    print_action,
    print_reflection_status,
    print_final_answer,
    print_divider,
    print_user_prompt,
    print_error,
    print_goodbye,
    print_help,
    thinking_spinner,
)
from utils.helpers import load_preferences
from utils.llm import chat_ollama, is_ollama_available
from utils.logger import get_logger
from utils.mcp_client import MCPClient
from utils.parser import parse_llm_json
from utils.prompts import SYSTEM_PROMPT, FORMAT_PROMPT
from utils.reflection import reflect

logger = get_logger(__name__, level=logging.WARNING)


# ---------------------------------------------------------------------------
# LLM call + JSON parse
# ---------------------------------------------------------------------------

def _ask_llm(messages: list[dict]) -> tuple[dict | None, str]:
    raw = chat_ollama(messages, temperature=0.1)
    return parse_llm_json(raw), raw


# ---------------------------------------------------------------------------
# MCP tool call
# ---------------------------------------------------------------------------

async def _call_tool(client: MCPClient, action: str, action_input: dict) -> str:
    try:
        return await client.call_tool(action, action_input)
    except ValueError:
        available = [t.name for t in client.get_tools()]
        return json.dumps({"error": f"Tool '{action}' not found. Available: {available}"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Ask LLM to format a tool result into human-readable text
# ---------------------------------------------------------------------------

def _format_with_llm(user_prompt: str, tool_name: str, raw_result: str) -> str:
    """Ask the LLM to turn a raw tool JSON result into a friendly answer."""
    prompt = FORMAT_PROMPT.format(
        user_prompt=user_prompt,
        tool_name=tool_name,
        tool_result=raw_result,
    )
    answer = chat_ollama(
        [{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    # If LLM returns empty or JSON, fall back to raw result
    stripped = answer.strip()
    if not stripped or stripped.startswith("{"):
        return raw_result
    return stripped


def format_book_result(raw_result: str) -> str:
    """Deterministically format a `book_recommend` tool JSON result into human text.

    Falls back to LLM formatting if the raw result isn't valid JSON or lacks expected fields.
    """
    try:
        data = json.loads(raw_result)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        title = data.get("title") or data.get("name") or "Unknown Title"
        author = data.get("author") or "Unknown Author"
        year = data.get("year") or "Unknown"
        summary = data.get("summary") or ""
        if isinstance(summary, list):
            summary_text = summary[0] if summary else ""
        else:
            summary_text = summary

        # Generate engaging description if empty or too short
        if not summary_text or len(summary_text) < 10:
            if is_ollama_available():
                prompt = (
                    f"Write a very brief, engaging 1-sentence description/hook for the book "
                    f"'{title}' by {author} ({year}). Do not mention page counts or metadata. "
                    f"Only return the description itself."
                )
                try:
                    desc = chat_ollama([{"role": "user", "content": prompt}], temperature=0.5).strip()
                    if desc.startswith('"') and desc.endswith('"'):
                        desc = desc[1:-1].strip()
                    if desc and not desc.startswith("{") and "error" not in desc.lower():
                        summary_text = desc
                except Exception:
                    pass

        parts = []
        parts.append(f"book name:- {title} ({year})")
        parts.append(f"author:- {author}")
        if summary_text:
            parts.append(f"description :- {summary_text}")
        return "\n".join(parts)
    except Exception:
        # Fall back to LLM formatting if JSON parsing fails
        return _format_with_llm("suggest a book", "book_recommend", raw_result)


def format_weather_result(raw_result: str) -> str:
    try:
        data = json.loads(raw_result)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        name = data.get("location") or data.get("location_name") or "Unknown location"
        temp = data.get("temperature_celsius")
        weather = data.get("weather")
        wind = data.get("wind_speed_kmh")
        tz = data.get("timezone")
        lat = data.get("latitude")
        lon = data.get("longitude")
        if lat is not None and lon is not None:
            return f"Weather for {name} (approx {lat:.4f}, {lon:.4f}): {temp}°C, {weather}, wind {wind} km/h (timezone: {tz})"
        return f"Weather for {name}: {temp}°C, {weather}, wind {wind} km/h (timezone: {tz})"
    except Exception:
        return _format_with_llm("get weather", "get_weather", raw_result)


def format_movie_result(raw_result: str) -> str:
    try:
        data = json.loads(raw_result)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        title = data.get("title") or "Unknown"
        rating = data.get("rating")
        year = data.get("year")
        overview = data.get("overview") or ""
        return f"movie name:- {title} ({year})\nrating:- {rating}/10\ndescription :- {overview}"
    except Exception:
        return _format_with_llm("recommend a movie", "recommend_movie", raw_result)


def format_joke_result(raw_result: str) -> str:
    try:
        data = json.loads(raw_result)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        if data.get("joke"):
            return data["joke"]
        setup = data.get("setup")
        punch = data.get("punchline") or data.get("delivery")
        if setup and punch:
            return f"{setup}\n{punch}"
        return json.dumps(data)
    except Exception:
        return _format_with_llm("tell a joke", "random_joke", raw_result)


def format_quote_result(raw_result: str) -> str:
    try:
        data = json.loads(raw_result)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        content = data.get("content") or data.get("quote")
        author = data.get("author")
        if content and author:
            return f'"{content}" — {author}'
        if content:
            return content
        return json.dumps(data)
    except Exception:
        return _format_with_llm("quote", "motivation_quote", raw_result)


def normalize_movie_request(user_input: str) -> str:
    text = user_input.lower()
    corrections = {
        "sugget": "suggest",
        "suggets": "suggest",
        "sugest": "suggest",
        "mudder": "murder",
        "muder": "murder",
        "mystrey": "mystery",
        "scifi": "sci-fi",
    }
    for typo, fix in corrections.items():
        text = re.sub(rf"\b{re.escape(typo)}\b", fix, text)

    # Remove common request words and punctuation
    text = re.sub(r"\b(suggest|recommend|please|can you|you|me|a|an|give|show|find)\b", "", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if "murder" in text and "mystery" in text:
        return "murder mystery"
    if "murder" in text:
        return "thriller"
    if "detective" in text or "whodunit" in text:
        return "murder mystery"
    if "mystery" in text:
        return "mystery"
    if "slasher" in text or "zombie" in text or "ghost" in text or "supernatural" in text:
        return "horror"
    if "action" in text:
        return "action"
    if "comedy" in text or "funny" in text:
        return "comedy"
    if "thriller" in text:
        return "thriller"
    if "sci" in text or "science fiction" in text or "sci-fi" in text:
        return "sci-fi"
    if "romance" in text or "romcom" in text:
        return "romance"
    return text or "horror"


# ---------------------------------------------------------------------------
# Main ReAct loop
# ---------------------------------------------------------------------------

async def run_react_loop(user_prompt: str, client: MCPClient) -> str:
    system_msg = SYSTEM_PROMPT.format(tools_description=client.tools_description())
    messages: list[dict] = [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": user_prompt},
    ]
    reasoning_chain: list[dict] = []
    final_answer = "I'm sorry, I couldn't find a good answer. Please try again!"

    for iteration in range(1, config.MAX_ITERATIONS + 1):

        with thinking_spinner(f"Thinking... (step {iteration}/{config.MAX_ITERATIONS})"):
            try:
                decision, raw_response = _ask_llm(messages)
            except RuntimeError as exc:
                print_error(str(exc))
                return str(exc)

        if decision is None:
            final_answer = raw_response.strip()
            break

        thought      = decision.get("thought", "")
        action       = decision.get("action", "FINISH").strip()
        action_input = decision.get("action_input", {})
        if not isinstance(action_input, dict):
            action_input = {}

        print_thought(thought, iteration)

        # ── FINISH ────────────────────────────────────────────────────────
        if action.upper() == "FINISH":
            raw_resp = action_input.get("response", "").strip()
            if raw_resp and raw_resp.lower() != "done":
                final_answer = raw_resp
            reasoning_chain.append({
                "thought": thought, "action": "FINISH",
                "action_input": action_input, "observation": "",
            })
            break

        # ── Unknown action with a response field → treat as FINISH ────────
        known_tools = {t.name for t in client.get_tools()}
        if action not in known_tools:
            fallback = action_input.get("response", "").strip()
            if fallback:
                final_answer = fallback
            reasoning_chain.append({
                "thought": thought, "action": "FINISH",
                "action_input": action_input, "observation": "",
            })
            break

        # ── Call tool ─────────────────────────────────────────────────────
        print_action(action, action_input)

        with thinking_spinner(f"Calling {action}..."):
            raw_observation = await _call_tool(client, action, action_input)

        reasoning_chain.append({
            "thought": thought, "action": action,
            "action_input": action_input, "observation": raw_observation,
        })

        # Tell the LLM what the tool returned and keep the conversation history
        messages.append({"role": "assistant", "content": raw_response})
        messages.append({"role": "user", "content": raw_observation})

        # Ask LLM to format the tool result into a human-readable answer
        with thinking_spinner("Formatting answer..."):
            final_answer = _format_with_llm(user_prompt, action, raw_observation)

        # Preserve the formatted response in the conversation history.
        messages.append({"role": "assistant", "content": final_answer})

    # ── Reflection ────────────────────────────────────────────────────────
    with thinking_spinner("Checking answer..."):
        corrected = reflect(reasoning_chain, final_answer)

    is_correct = (corrected.strip() == final_answer.strip())
    print_reflection_status(is_correct)
    return corrected


# ---------------------------------------------------------------------------
# Slash-command handler
# ---------------------------------------------------------------------------

def _handle_command(cmd: str, client: MCPClient) -> bool:
    cmd = cmd.strip().lower()
    if cmd == "/tools":
        for tool in client.get_tools():
            console.print(
                f"  [yellow bold]✓[/] [bright_white]{tool.name}[/]  "
                f"[grey50]{(tool.description or '')[:70]}[/]"
            )
        return True
    if cmd == "/prefs":
        prefs = load_preferences(config.PREFERENCES_FILE)
        if prefs:
            for k, v in prefs.items():
                console.print(f"  [cyan]{k}[/]: [white]{v}[/]")
        else:
            console.print("  [grey50]No preferences saved yet.[/]")
        return True
    if cmd == "/clear":
        console.clear()
        print_banner()
        return True
    if cmd == "/help":
        print_help()
        return True
    return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    print_banner()

    with thinking_spinner("Checking LLM availability..."):
        available = is_ollama_available()

    use_llm = bool(available)
    if use_llm:
        console.print(f"  [green]✓[/] Ollama connected  [grey50](model: {config.OLLAMA_MODEL})[/]\n")
    else:
        console.print(f"  [yellow]⚠[/] Ollama not available — running in deterministic-only mode\n")

    client = MCPClient()
    project_root = Path(__file__).resolve().parent

    for alias, script in [
        ("info", "info_server.py"),
        ("fun",  "fun_server.py"),
    ]:
        with thinking_spinner(f"Connecting to {alias} server..."):
            try:
                await client.connect(
                    command=sys.executable,
                    args=[str(project_root / "servers" / script)],
                    alias=alias,
                )
            except Exception as exc:
                print_error(f"Could not connect to {alias} server: {exc}")

    with thinking_spinner("Discovering tools..."):
        await client.discover_tools()

    print_server_status(client.get_session_names(), client.get_tools())
    console.print("  [grey50]Type [white]/help[/] for commands · [white]quit[/] to exit[/]\n")
    print_divider()

    try:
        while True:
            user_input = print_user_prompt()

            if not user_input:
                print_goodbye()
                break

            if user_input.lower() in {"quit", "exit", "bye", "q"}:
                print_goodbye()
                break

            if user_input.startswith("/"):
                if not _handle_command(user_input, client):
                    console.print(f"  [red]Unknown command:[/] {user_input}  [grey50](try /help)[/]")
                print_divider()
                continue

            console.print()

            # Quick intent shortcuts: handle common tool requests directly
            # This avoids the LLM failing to pick the `book_recommend` tool for short/typo'd queries.
            lowered = user_input.lower()
            # Book suggestions
            if any(k in lowered for k in ("suggest", "suggest me", "recommend", "suggets", "sugest", "suggestion")) and \
               ("book" in lowered or "novel" in lowered or "mystery" in lowered or "mudder" in lowered or "muder" in lowered):
                try:
                    raw = await client.call_tool("book_recommend", {"topic": user_input})
                    formatted = format_book_result(raw)
                    print_final_answer(formatted)
                except Exception as exc:
                    print_error(f"Book shortcut failed: {exc}")
                print_divider()
                continue

            # Weather by city
            if any(k in lowered for k in ("weather", "temperature", "forecast")) and (
                any(c in lowered for c in (
                    "city", ",", "surat", "ahmedabad", "ahmeadabad", "vadodara",
                    "gujarat", "india", "location", "place",
                ))
                or "weather of" in lowered
                or "weather in" in lowered
                or "temperature in" in lowered
            ):
                try:
                    # try get_weather_by_city first
                    raw = await client.call_tool("get_weather_by_city", {"city": user_input})
                    formatted = format_weather_result(raw)
                    print_final_answer(formatted)
                except Exception as exc:
                    print_error(f"Weather shortcut failed: {exc}")
                print_divider()
                continue

            # Movie recommendation shortcut
            if any(k in lowered for k in ("recommend movie", "suggest movie", "movie", "recommend a movie", "suggest a movie")) or ("movie" in lowered and any(g in lowered for g in ("horror","sci","sci-fi","action","comedy","murder","mystery","thriller"))):
                try:
                    genre = normalize_movie_request(user_input)
                    raw = await client.call_tool("recommend_movie", {"genre": genre})
                    formatted = format_movie_result(raw)
                    print_final_answer(formatted)
                except Exception as exc:
                    print_error(f"Movie shortcut failed: {exc}")
                print_divider()
                continue

            # Jokes / quotes
            if any(k in lowered for k in ("joke", "tell me a joke", "funny")):
                try:
                    raw = await client.call_tool("random_joke", {})
                    formatted = format_joke_result(raw)
                    print_final_answer(formatted)
                except Exception as exc:
                    print_error(f"Joke shortcut failed: {exc}")
                print_divider()
                continue

            if any(k in lowered for k in ("quote", "motiv", "inspir")):
                try:
                    raw = await client.call_tool("motivation_quote", {})
                    formatted = format_quote_result(raw)
                    print_final_answer(formatted)
                except Exception as exc:
                    print_error(f"Quote shortcut failed: {exc}")
                print_divider()
                continue

            try:
                answer = await run_react_loop(user_input, client)
                print_final_answer(answer)
            except Exception as exc:
                print_error(f"Something went wrong: {exc}")

            print_divider()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
