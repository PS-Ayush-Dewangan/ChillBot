# ChillBot — API Reference

All tools are exposed via MCP servers and discovered dynamically by the agent.

---

## Info Server (`servers/info_server.py`)

### `get_weather`
Get current weather conditions for a geographic location.

**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `latitude` | float | ✓ | Geographic latitude (e.g. `51.5` for London) |
| `longitude` | float | ✓ | Geographic longitude (e.g. `-0.1` for London) |

**Returns** JSON object:
```json
{
  "temperature_celsius": 18.5,
  "weather": "Partly cloudy",
  "wind_speed_kmh": 12.3,
  "timezone": "Europe/London",
  "latitude": 51.5,
  "longitude": -0.1
}
```

**Data source:** [Open-Meteo](https://open-meteo.com/) (free, no API key required)

---

### `book_recommend`
Recommend a book on a given topic.

**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic` | string | ✓ | Subject or keyword (e.g. `"space exploration"`) |

**Returns** JSON object:
```json
{
  "title": "A Brief History of Time",
  "author": "Stephen Hawking",
  "year": 1988,
  "topic": "space"
}
```

**Data source:** [Open Library](https://openlibrary.org/developers/api) (free)

---

### `recommend_movie`
Recommend a movie for a given genre.

**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `genre` | string | ✓ | Movie genre (e.g. `"sci-fi"`, `"comedy"`, `"horror"`) |

**Returns** JSON object:
```json
{
  "title": "Inception",
  "rating": 8.8,
  "overview": "A thief who steals corporate secrets...",
  "year": "2010",
  "genre": "sci-fi",
  "source": "TMDB"
}
```

**Data source:** [TMDB](https://www.themoviedb.org/) (TMDB API key required in production)

---

## Fun Server (`servers/fun_server.py`)

### `random_joke`
Fetch a random joke.

**Parameters:** None

**Returns** JSON object:
```json
{ "setup": "Why don't scientists trust atoms?", "punchline": "Because they make up everything!" }
```
or for single-part jokes:
```json
{ "joke": "I told my wife she was drawing her eyebrows too high. She looked surprised." }
```

**Data source:** [JokeAPI](https://v2.jokeapi.dev/)

---

### `motivation_quote`
Fetch a motivational quote.

**Parameters:** None

**Returns** JSON object:
```json
{ "content": "The only way to do great work is to love what you do.", "author": "Steve Jobs" }
```

**Data source:** [Quotable API](https://api.quotable.io/)
