# ChillBot — Setup Guide

## Prerequisites

- Python 3.11 or higher
- [Ollama](https://ollama.com/) installed and running locally
- Git

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/your-username/chillbot.git
cd chillbot
```

---

## Step 2 — Create a Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4 — Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Open `.env` and set your values:

```env
OLLAMA_MODEL=mistral:7b
OLLAMA_HOST=http://localhost:11434
TMDB_API_KEY=          # Required for live movie recommendations in production
MAX_ITERATIONS=5
TIMEOUT=15
```

---

## Step 5 — Install and Start Ollama

1. Download Ollama from [https://ollama.com/download](https://ollama.com/download)
2. Start the Ollama server:
   ```bash
   ollama serve
   ```
3. Pull the default model:
   ```bash
   ollama pull mistral:7b
   ```

> **Tip:** You can use a smaller/faster model by changing `OLLAMA_MODEL` in `.env`.
> For example: `OLLAMA_MODEL=llama3.2:3b`

---

## Step 6 — (Optional) Get a TMDB API Key

For live movie recommendations:

1. Create a free account at [https://www.themoviedb.org/](https://www.themoviedb.org/)
2. Go to **Settings → API** and request a free API key.
3. Add it to your `.env`: `TMDB_API_KEY=your_key_here`

If you skip this step, movie recommendations will be disabled in production.

---

## Step 7 — Run ChillBot

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

✓ Ollama connected  (model: mistral:7b)

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

## Step 8 — Run Tests

```bash
pytest tests/ -v
```

---

## Troubleshooting

### "Cannot connect to Ollama"
- Make sure `ollama serve` is running in a separate terminal.
- Check that `OLLAMA_HOST` in `.env` matches the address Ollama is listening on.

### "Model not found"
- Run `ollama pull mistral:7b` (or whichever model is set in `OLLAMA_MODEL`).

### Slow responses
- The first response after starting Ollama may be slow while the model loads into memory.
- Subsequent responses will be faster.
- Consider using a smaller model like `llama3.2:3b` for faster responses.

### Tool not found errors
- Ensure all three server files exist in the `servers/` directory.
- Check that `mcp` is installed: `pip show mcp`
