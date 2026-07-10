# ChillBot — Architecture Overview

## System Design

ChillBot is a locally-running AI agent that follows the **ReAct** (Reason + Act) pattern.
The LLM reasons about the user's request, decides which tool to call, observes the result,
and repeats until it has enough information to produce a final answer.

---

## High-Level Flow

```
User Input (terminal)
        │
        ▼
   ┌─────────┐
   │  Agent  │  ← agent.py
   └────┬────┘
        │  Build prompt with tool descriptions
        ▼
   ┌─────────┐
   │   LLM   │  ← utils/llm.py  (Ollama / mistral:7b)
   └────┬────┘
        │  Returns JSON: { thought, action, action_input }
        ▼
   ┌────────────┐
   │ MCP Client │  ← utils/mcp_client.py
   └─────┬──────┘
         │  Dispatches to the correct server
    ┌────┴──────────────────────┐
     │                           │
     ▼                           ▼
┌──────────┐  ┌──────────┐
│   Info   │  │   Fun    │
│  Server  │  │  Server  │
└──────────┘  └──────────┘
     │               │
     ▼               ▼
 Weather         Jokes
 Books           Quotes
 Movies
        │
        ▼
   Observation fed back to LLM
        │
        ▼  (repeat up to MAX_ITERATIONS)
   ┌────────────┐
   │ Reflection │  ← utils/reflection.py
   └─────┬──────┘
         │  Verifies / corrects the answer
         ▼
   Final Response printed to terminal
```

---

## Components

### agent.py
The orchestrator. Runs the ReAct loop, manages conversation history,
calls the MCP client, and invokes reflection before printing the answer.

### utils/llm.py
Thin wrapper around the Ollama REST API. Supports both single-turn
(`query_ollama`) and multi-turn (`chat_ollama`) requests.

### utils/mcp_client.py
Manages stdio connections to all three MCP servers. Discovers tools
dynamically at startup and routes `call_tool()` to the correct server.

### utils/prompts.py
All LLM prompt templates in one place: system prompt, reflection prompt,
JSON repair prompt, and tool selection hint.

### utils/parser.py
Extracts JSON from raw LLM output (handles markdown fences, whitespace).
Falls back to a second LLM pass to repair malformed JSON.

### utils/reflection.py
After the ReAct loop finishes, asks the LLM to review the reasoning chain
and correct any mistakes before the answer is shown to the user.

### utils/helpers.py
Shared utilities: HTTP GET with retry/timeout, JSON file I/O,
and preferences management.

### utils/logger.py
Colored console logger with timestamps used across all modules.

---

## MCP Servers

Each server is an independent Python process launched via stdio transport.

| Server | File | Tools |
|--------|------|-------|
| Info | `servers/info_server.py` | `get_weather`, `book_recommend`, `recommend_movie` |
| Fun | `servers/fun_server.py` | `random_joke`, `motivation_quote` |

---

## ReAct Loop Detail

```
iteration = 1
while iteration <= MAX_ITERATIONS:
    response = LLM(conversation_history)
    decision = parse_json(response)

    if decision.action == "FINISH":
        final_answer = decision.action_input.response
        break

    observation = MCP.call_tool(decision.action, decision.action_input)
    conversation_history.append(observation)
    iteration += 1

final_answer = reflect(reasoning_chain, final_answer)
print(final_answer)
```

---

## Data Flow for a Sample Prompt

**Prompt:** "Recommend a sci-fi movie"

1. Agent builds system prompt listing available tools.
2. LLM responds: `{"thought": "User wants a sci-fi movie", "action": "recommend_movie", "action_input": {"genre": "sci-fi"}}`
3. MCP client routes to `info_server.py → recommend_movie("sci-fi")`.
4. Server queries TMDB and returns movie JSON.
5. LLM receives observation and responds: `{"action": "FINISH", "action_input": {"response": "🎬 Here's a great sci-fi pick: ..."}}`
6. Reflection confirms the answer is correct.
7. Final answer printed to terminal.
