<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Ollama-✓-green?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama">
  <img src="https://img.shields.io/badge/MCP-✓-purple?style=for-the-badge" alt="MCP">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" alt="Active">
</p>

<div align="center">
  <h1>🤖 ChillBot</h1>
  <p><strong>AI-Powered Personal Companion</strong></p>
  <p><em>Built with Model Context Protocol (MCP) · Ollama · ReAct Agent Loop</em></p>
  <p>Runs 100% locally — no cloud, no API costs, full privacy.</p>
</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Tool Reference](#-tool-reference)
- [APIs & Data Sources](#-apis--data-sources)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧠 Overview

ChillBot is a **locally-running AI agent** that combines the power of large language models (via Ollama) with a dynamic tool ecosystem (via MCP). Unlike traditional chatbots with hardcoded workflows, ChillBot uses a **ReAct (Reason + Act) loop** — the LLM autonomously decides which tools to call, interprets their results, and refines its responses through iterative reasoning and self-reflection.

**Key differentiators:**
- 🏠 **100% local** — No data leaves your machine
- 🧩 **Dynamic tool discovery** — Tools are discovered at runtime, not hardcoded
- 🔄 **Self-reflective** — The agent reviews and corrects its own answers
- 🔌 **Extensible** — Add new capabilities by writing simple MCP servers
- 🎨 **Rich CLI** — Colored terminal output with emoji-rich responses

---

## ✨ Features

### Core AI Capabilities

| Feature | Description |
|---------|-------------|
| 🧠 **True AI Agent** | The LLM decides which tools to call at runtime — no hardcoded workflows or if-else chains |
| 🔄 **ReAct Loop** | Reason → Act → Observe → Repeat → Reflect — iterative problem-solving |
| 🔍 **Self-Reflection** | Post-reasoning verification catches and corrects mistakes before showing the answer |
| 🔧 **JSON Repair** | Automatically fixes malformed LLM output using a secondary LLM pass |
| 💾 **Preference Memory** | Remembers your favorite genres, topics, and preferences across sessions |

### Tool Ecosystem

| Tool | Description | Data Source |
|------|-------------|-------------|
| 🌤️ **Weather** | Live weather conditions for any location | Open-Meteo (free, no API key) |
| 📚 **Books** | Book recommendations by topic or genre | Open Library (free) |
| 🎬 **Movies** | Movie recommendations by genre | TMDB (free API key optional) |
| 😂 **Jokes** | Random jokes (single or two-part) | JokeAPI (free) |
| 💪 **Quotes** | Motivational and inspirational quotes | Quotable API (free) |

### User Experience

- 🎨 **Rich terminal UI** with colors, emojis, and formatted output
- ⌨️ **Slash commands** (`/tools`, `/prefs`, `/clear`, `/help`)
- ⚡ **Smart shortcuts** — common requests bypass the LLM for instant responses
- 🧹 **Typo-tolerant** — understands "sugget a mudder mystrey" → "suggest a murder mystery"

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER TERMINAL                                │
│  "What's the weather in London?" / "Recommend a sci-fi movie"       │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         AGENT (agent.py)                             │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    ReAct Loop (1..MAX_ITERATIONS)             │   │
│  │                                                              │   │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐              │   │
│  │   │  REASON  │───▶│   ACT    │───▶│  OBSERVE │──┐           │   │
│  │   │ (LLM     │    │ (Call    │    │ (Tool    │  │           │   │
│  │   │  thinks) │    │  tool)   │    │  result) │  │           │   │
│  │   └──────────┘    └──────────┘    └──────────┘  │           │   │
│  │         ▲                                        │           │   │
│  │         └────────────────────────────────────────┘           │   │
│  │                      (repeat if needed)                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    REFLECTION (reflection.py)                 │   │
│  │  "Does the answer make sense? Is it complete? Correct it."   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│                     FINAL ANSWER 🎉                                 │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            │  Tool calls via MCP
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      MCP CLIENT (mcp_client.py)                      │
│                                                                      │
│  ┌─────────────────────┐    ┌─────────────────────┐                 │
│  │   Info Server       │    │   Fun Server        │                 │
│  │   (stdio transport) │    │   (stdio transport) │                 │
│  └──────────┬──────────┘    └──────────┬──────────┘                 │
│             │                          │                            │
└─────────────┼──────────────────────────┼────────────────────────────┘
              │                          │
              ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│   🌤️ get_weather    │    │   😂 random_joke    │
│   📚 book_recommend │    │   💪 motivation_quote│
│   🎬 recommend_movie│    │                     │
└─────────────────────┘    └─────────────────────┘
              │                          │
              ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│   Open-Meteo        │    │   JokeAPI           │
│   Open Library      │    │   Quotable API      │
│   TMDB              │    │                     │
└─────────────────────┘    └─────────────────────┘
```

---

## 🔄 How It Works

### The ReAct Loop (Step by Step)

ChillBot follows the **ReAct** (Reasoning + Acting) pattern, a technique that combines chain-of-thought reasoning with tool use:

```
Step 1: REASON
  LLM receives: user prompt + system prompt (with tool descriptions)
  LLM outputs:  { "thought": "User wants weather in London",
                   "action": "get_weather",
                   "action_input": { "latitude": 51.5, "longitude": -0.1 } }

Step 2: ACT
  MCP Client routes the call to the correct server
  Server queries the external API and returns structured JSON

Step 3: OBSERVE
  Raw tool result is fed back to the LLM:
  { "temperature_celsius": 18.5, "weather": "Partly cloudy", ... }

Step 4: REPEAT or FINISH
  LLM decides: call another tool OR produce final answer
  { "action": "FINISH", "action_input": { "response": "🌤️ London: 18.5°C..." } }

Step 5: REFLECT
  Reflection module reviews the reasoning chain
  Verifies correctness, catches hallucinations, corrects mistakes

Step 6: OUTPUT
  Final answer printed to terminal with rich formatting
```

### Smart Shortcuts

For common requests, ChillBot bypasses the LLM entirely for **instant responses**:

- `"weather in London"` → directly calls `get_weather_by_city`
- `"suggest a sci-fi movie"` → directly calls `recommend_movie`
- `"tell me a joke"` → directly calls `random_joke`
- `"motivate me"` → directly calls `motivation_quote`

This ensures snappy responses for frequent tasks while keeping the full ReAct loop available for complex, multi-step queries.

---

## 📁 Project Structure

```
chillbot/
│
├── agent.py                  # 🧠 Main AI agent — ReAct loop orchestrator
├── config.py                 # ⚙️ Centralized configuration (loads .env)
├── preferences.json          # 💾 User preferences (auto-saved)
│
├── servers/                  # 🛠️ MCP Tool Servers
│   ├── info_server.py        #   🌤️ Weather · 📚 Books · 🎬 Movies
│   └── fun_server.py         #   😂 Jokes · 💪 Quotes
│
├── utils/                    # 🔧 Core Utilities
│   ├── cli.py                #   🎨 Terminal UI (colors, formatting)
│   ├── llm.py                #   🤖 Ollama API wrapper
│   ├── mcp_client.py         #   🔌 MCP connection manager
│   ├── prompts.py            #   📝 All LLM prompt templates
│   ├── parser.py             #   🔍 JSON extraction & repair
│   ├── reflection.py         #   ✅ Post-reasoning answer verification
│   ├── logger.py             #   📋 Colored logging
│   └── helpers.py            #   🛠️ HTTP, JSON, preferences utilities
│
├── tests/                    # 🧪 Test Suite
│   ├── test_books.py         #   Book recommendation tests
│   ├── test_movies.py        #   Movie recommendation tests
│   └── test_weather.py       #   Weather tool tests
│
├── docs/                     # 📖 Documentation
│   ├── architecture.md       #   Detailed architecture overview
│   ├── api_reference.md      #   Complete API reference
│   └── setup_guide.md        #   Step-by-step setup guide
│
├── scripts/                  # 📜 Helper Scripts
│   ├── test_book_shortcut.py #   Book shortcut test
│   ├── test_formatters.py    #   Formatter tests
│   └── test_mcp_servers.py   #   MCP server integration tests
│
├── screenshots/              # 📸 Screenshots
│   ├── architecture.png      #   Architecture diagram
│   ├── demo1.png             #   Usage demo
│   └── demo2.png             #   Usage demo
│
├── .env.example              # 📄 Environment template
├── .gitignore                # 🙈 Git ignore rules
├── pyproject.toml            # 📦 Project metadata & dependencies
├── requirements.txt          # 📦 Python dependencies
└── README.md                 # 📖 This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **Ollama** — [Download](https://ollama.com/download) (for local LLM inference)
- **Git** — [Download](https://git-scm.com/downloads)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/chillbot.git
cd chillbot

# 2. Create and activate a virtual environment
# Windows:
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set OLLAMA_MODEL, optionally TMDB_API_KEY
```

### Start Ollama

```bash
# Terminal 1: Start the Ollama server
ollama serve

# Terminal 2: Pull the default model
ollama pull llama3.2:1b
```

### Run ChillBot

```bash
python agent.py
```

You should see:

```
================================================
🤖  ChillBot
    AI Personal Companion
    Powered by MCP + Ollama
================================================

✓ Ollama connected  (model: llama3.2:1b)

Connecting to MCP servers…
Connected MCP Servers:
  ✓ Info Server
  ✓ Fun Server

Discovered Tools:
  ✓ get_weather
  ✓ book_recommend
  ✓ recommend_movie
  ✓ random_joke
  ✓ motivation_quote

Type your message below. Type 'quit' or 'exit' to stop.
──────────────────────────────────────────────────

🧑 You:
```

---

## 💬 Usage Guide

### Example Prompts

| Prompt | What Happens |
|--------|-------------|
| `What's the weather in London?` | 🌤️ Fetches live weather via Open-Meteo |
| `Recommend a sci-fi movie` | 🎬 Searches TMDB for sci-fi recommendations |
| `Tell me a joke` | 😂 Fetches a random joke from JokeAPI |
| `Motivate me` | 💪 Gets an inspirational quote |
| `Recommend a book about space exploration` | 📚 Searches Open Library for space books |
| `Suggest a murder mystery movie` | 🎬 Smart genre normalization → "murder mystery" |
| `What's the temperature in Tokyo?` | 🌤️ Weather shortcut (bypasses LLM) |

### Slash Commands

| Command | Description |
|---------|-------------|
| `/tools` | List all discovered MCP tools |
| `/prefs` | Show saved user preferences |
| `/clear` | Clear the terminal screen |
| `/help` | Show help information |

### Exit Commands

Type `quit`, `exit`, `bye`, or `q` to exit ChillBot.

---

## 🛠️ Tool Reference

### `get_weather`
Get current weather conditions for any location.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `latitude` | float | ✓ | Geographic latitude (e.g. `51.5`) |
| `longitude` | float | ✓ | Geographic longitude (e.g. `-0.1`) |

**Returns:** Temperature, weather description, wind speed, timezone

### `book_recommend`
Recommend a book on a given topic.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `topic` | string | ✓ | Subject or keyword (e.g. `"space exploration"`) |

**Returns:** Title, author, publication year

### `recommend_movie`
Recommend a movie for a given genre.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `genre` | string | ✓ | Movie genre (e.g. `"sci-fi"`, `"comedy"`) |

**Returns:** Title, rating, overview, year

### `random_joke`
Fetch a random joke. No parameters required.

### `motivation_quote`
Fetch a motivational quote. No parameters required.

> 📖 **Full API documentation** → [docs/api_reference.md](docs/api_reference.md)

---

## 🔌 APIs & Data Sources

| API | Purpose | API Key Required | Rate Limit |
|-----|---------|-----------------|------------|
| [Open-Meteo](https://open-meteo.com/) | Weather data | ❌ No | Generous |
| [Open Library](https://openlibrary.org/developers/api) | Book data | ❌ No | Generous |
| [TMDB](https://www.themoviedb.org/) | Movie data | ✅ Optional | 40 req/10s |
| [JokeAPI](https://v2.jokeapi.dev/) | Jokes | ❌ No | Generous |
| [Quotable API](https://api.quotable.io/) | Quotes | ❌ No | 150 req/min |

> **Note:** All APIs except TMDB are completely free with no registration required. TMDB only needs an API key for production use — the agent will still work without it.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_weather.py -v
pytest tests/test_books.py -v
pytest tests/test_movies.py -v

# Run with coverage (if pytest-cov is installed)
pytest tests/ -v --cov=.
```

---

## 🔧 Troubleshooting

### "Cannot connect to Ollama"
- Ensure `ollama serve` is running in a separate terminal
- Verify `OLLAMA_HOST` in `.env` matches Ollama's address (default: `http://localhost:11434`)
- Check if Ollama is installed: `ollama --version`

### "Model not found"
- Pull the model: `ollama pull llama3.2:1b`
- Or change the model in `.env`: `OLLAMA_MODEL=llama3.2:1b`

### Slow responses
- First response is slow while the model loads into GPU memory
- Use a smaller model: `OLLAMA_MODEL=llama3.2:1b` or `OLLAMA_MODEL=phi3:mini`
- Reduce `MAX_ITERATIONS` in `.env` (default: 5)

### "Tool not found"
- Ensure all server files exist in `servers/` directory
- Verify MCP is installed: `pip show mcp`
- Check for Python import errors in server files

### Windows-specific
- Use `python` not `python3`
- Virtual environment: `.venv\Scripts\activate`
- Path separator: Use `\` or `/` — Python handles both

---

## 🗺️ Roadmap

- [ ] 🌐 **Web UI** — Streamlit or Gradio interface
- [ ] 💬 **Conversation Memory** — Persistent chat history across sessions
- [ ] 🎤 **Voice Input/Output** — Speech-to-text and text-to-speech
- [ ] 📅 **Calendar Integration** — MCP server for calendar management
- [ ] 📧 **Email Integration** — MCP server for email
- [ ] 📰 **News Server** — Latest news headlines
- [ ] 🐳 **Docker Support** — Containerized deployment
- [ ] ⚡ **Streaming Responses** — Real-time token-by-token output
- [ ] 🔌 **Plugin System** — Community-contributed MCP servers

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **🐛 Report bugs** — Open an issue with reproduction steps
2. **💡 Suggest features** — Open an issue with your idea
3. **🔧 Submit PRs** — Fix bugs or add features

### Development Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

### Adding a New Tool

1. Create a new MCP server in `servers/` (or add to an existing one)
2. Register the tool using the `@server.tool()` decorator
3. The agent will automatically discover it at runtime — no code changes needed!

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/your-username">ChillBot</a>
  <br>
  <sub>Powered by Ollama · MCP · Python</sub>
</p>
