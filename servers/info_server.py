"""
info_server.py — MCP Info Server for ChillBot.

Provides tools for real-world information:
  • get_weather      — current conditions via Open-Meteo
  • book_recommend   — book suggestions via Open Library
  • recommend_movie  — movie suggestions via TMDB
"""

import io
import json
import random
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from mcp.server.fastmcp import FastMCP
from utils.helpers import http_get
from utils.logger import get_logger
import config
import requests
import re

logger = get_logger(__name__)


def _nearest_city(latitude: float, longitude: float) -> str | None:
    """Return a nearby major city name if within ~50 km, otherwise None.

    This is a small static fallback for common Gujarat cities to ensure
    user-expected names like 'Surat' or 'Ahmedabad' are returned when
    reverse geocoding yields only administrative subdivisions.
    """
    from math import radians, sin, cos, asin, sqrt

    def haversine(lat1, lon1, lat2, lon2):
        # radius of Earth in km
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return R * c

    # Small list of Gujarat cities (lat, lon)
    cities = {
        "Surat": (21.1702, 72.8311),
        "Ahmedabad": (23.0225, 72.5714),
        "Vadodara": (22.3072, 73.1812),
        "Rajkot": (22.3039, 70.8022),
        "Bhavnagar": (21.7650, 72.1360),
    }

    for name, (clat, clon) in cities.items():
        if haversine(latitude, longitude, clat, clon) <= 50.0:
            return f"{name}, India"
    return None

# Minimal fallback movie recommendations when TMDB is unavailable.
_MOVIE_FALLBACKS: dict[str, list[dict[str, str | float]]] = {
    "horror": [
        {
            "title": "The Conjuring",
            "rating": 7.5,
            "overview": "Paranormal investigators help a family terrorized by a dark presence in their farmhouse.",
            "year": "2013",
            "genre": "horror",
            "source": "fallback",
        },
        {
            "title": "A Quiet Place",
            "rating": 7.5,
            "overview": "A family must live in silence to avoid blind creatures that hunt by sound.",
            "year": "2018",
            "genre": "horror",
            "source": "fallback",
        },
        {
            "title": "Get Out",
            "rating": 7.7,
            "overview": "A young Black man uncovers terrifying secrets when he meets his white girlfriend's family.",
            "year": "2017",
            "genre": "horror",
            "source": "fallback",
        },
    ],
    "sci-fi": [
        {
            "title": "Inception",
            "rating": 8.8,
            "overview": "A thief who steals corporate secrets through dream-sharing technology is given one last job.",
            "year": "2010",
            "genre": "sci-fi",
            "source": "fallback",
        },
    ],
    "mystery": [
        {
            "title": "Knives Out",
            "rating": 7.9,
            "overview": "A modern whodunit where a detective investigates a wealthy family's secrets.",
            "year": "2019",
            "genre": "mystery",
            "source": "fallback",
        },
        {
            "title": "Mystic River",
            "rating": 7.7,
            "overview": "Three childhood friends are reunited by a tragic murder and a police investigation.",
            "year": "2003",
            "genre": "mystery",
            "source": "fallback",
        },
        {
            "title": "Zodiac",
            "rating": 7.9,
            "overview": "A cartoonist becomes an amateur detective obsessed with the Zodiac killer investigation.",
            "year": "2007",
            "genre": "mystery",
            "source": "fallback",
        },
    ],
}

mcp = FastMCP("ChillBot Info Server")

# ---------------------------------------------------------------------------
# Tool 1 — Weather
# ---------------------------------------------------------------------------

@mcp.tool()
def get_weather(latitude: float, longitude: float) -> str:
    """
    Get current weather conditions for a location.

    Args:
        latitude:  Geographic latitude (e.g. 51.5 for London).
        longitude: Geographic longitude (e.g. -0.1 for London).

    Returns:
        JSON string with temperature, weather description, wind speed, and timezone.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
        "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m",
        "timezone": "auto",
        # Request windspeed in km/h to report friendly units
        "windspeed_unit": "kmh",
    }

    data = http_get(url, params=params)
    if not data:
        return json.dumps({"error": "Weather data unavailable. Please try again later."})

    current = data.get("current_weather", {})
    timezone = data.get("timezone", "Unknown")

    # Try to get a human-friendly location name via Open-Meteo reverse geocoding
    location_name = None
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/reverse"
        geo_params = {"latitude": latitude, "longitude": longitude, "count": 1, "language": "en"}
        geo = http_get(geo_url, params=geo_params)
        if geo and geo.get("results"):
            place = geo["results"][0]
            # Prefer city / name then admin1 / country for clarity
            parts = [place.get("name"), place.get("admin1"), place.get("country")]
            location_name = ", ".join([p for p in parts if p])
    except Exception:
        # Non-fatal: geocoding may fail in restricted networks
        location_name = None
    # If Open-Meteo geocoding wasn't available, try a lightweight Nominatim lookup
    if not location_name:
        try:
            nom_url = "https://nominatim.openstreetmap.org/reverse"
            headers = {"User-Agent": "ChillBot/1.0 (contact: dev@local)"}
            # Try multiple zoom levels from most-specific down to broader
            for zoom in (18, 16, 14, 13, 12, 10):
                try:
                    nom_params = {"format": "jsonv2", "lat": latitude, "lon": longitude, "zoom": zoom, "addressdetails": 1}
                    resp = requests.get(nom_url, params=nom_params, headers=headers, timeout=5)
                    if resp.status_code != 200:
                        continue
                    j = resp.json()
                    addr = j.get("address", {})
                    # Prefer explicit city/town/village/municipality
                    name = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality")
                    # If any address field mentions 'Surat' (or other major city), prefer that
                    combined = " ".join([str(v) for v in addr.values() if v])
                    if "surat" in combined.lower():
                        cand = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or addr.get("state")
                        if cand:
                            location_name = f"{cand}, {addr.get('country', '')}".strip().strip(',')
                            break
                    if name:
                        if addr.get("country"):
                            location_name = f"{name}, {addr.get('country')}"
                        else:
                            location_name = name
                        break
                    # Otherwise, if display_name present at fine zoom, use its first token
                    if j.get("display_name") and zoom >= 13:
                        display = j.get("display_name")
                        first = display.split(",")[0].strip()
                        for suffix in ["Taluka", "taluka", "District", "district"]:
                            if first.endswith(suffix):
                                first = first.rsplit(" ", 1)[0]
                        location_name = first
                        break
                except Exception:
                    continue
        except Exception:
            # Ignore geocoding failures — we'll return coordinates if name not found
            location_name = location_name

    # WMO weather interpretation codes → human-readable descriptions
    wmo_codes: dict[int, str] = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
        55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
    }

    weather_code = current.get("weathercode", -1)
    description = wmo_codes.get(weather_code, f"Weather code {weather_code}")

    result = {
        "temperature_celsius": current.get("temperature"),
        "weather": description,
        "wind_speed_kmh": current.get("windspeed"),
        "timezone": timezone,
        "location_name": location_name,
        "latitude": latitude,
        "longitude": longitude,
    }

    # If reverse geocoding returned a taluka/district name, prefer a nearby major city
    if not location_name or any(suffix in str(location_name).lower() for suffix in ["taluka", "district"]):
        near = _nearest_city(latitude, longitude)
        if near:
            result["location_name"] = near

    logger.info("Weather fetched for (%.2f, %.2f): %s", latitude, longitude, description)
    return json.dumps(result)


def _normalize_city_query(city: str) -> str:
    city_text = (city or "").strip()
    city_text = re.sub(r"\s+", " ", city_text)
    patterns = [
        r"^(?:tell me|show me|give me|what(?:'s| is)|please)\s+(?:the\s+)?(?:weather|forecast)\s*(?:of|in|for)?\s*(.+)$",
        r"^(?:weather|forecast)\s*(?:of|in|for)\s*(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, city_text, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip(" ?.!",)
            if extracted:
                return extracted
    return city_text


@mcp.tool()
def get_weather_by_city(city: str) -> str:
    """
    Resolve a city name to coordinates, fetch weather, and return a readable summary.

    Args:
        city: City or place name (e.g. 'Surat', 'Ahmedabad, India')

    Returns:
        Human-readable string with location, temperature, weather, wind, and timezone.
    """
    try:
        nom_url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "ChillBot/1.0 (contact: dev@local)"}
        query = _normalize_city_query(city)
        params = {"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1}
        resp = requests.get(nom_url, params=params, headers=headers, timeout=5)
        if resp.status_code != 200:
            return json.dumps({"error": f"Geocoding failed for '{city}' (status {resp.status_code})"})
        results = resp.json()
        if not results:
            return json.dumps({"error": f"Could not geocode location: '{city}'"})

        place = results[0]
        lat = float(place.get("lat"))
        lon = float(place.get("lon"))
        # Prefer the resolved name from the geocoder when present
        resolved = None
        addr = place.get("address", {})
        resolved = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or place.get("display_name")

        raw = get_weather(lat, lon)
        try:
            data = json.loads(raw)
        except Exception:
            return json.dumps({"error": "Failed to parse weather response"})

        name = data.get("location_name") or resolved or city
        temp = data.get("temperature_celsius")
        weather = data.get("weather")
        wind = data.get("wind_speed_kmh")
        tz = data.get("timezone")

        summary = (
            f"Weather for {name} (approx {lat:.4f}, {lon:.4f}):\n"
            f"• Temperature: {temp}°C\n"
            f"• Conditions: {weather}\n"
            f"• Wind: {wind} km/h\n"
            f"• Timezone: {tz}"
        )

        result = {
            "location": name,
            "latitude": lat,
            "longitude": lon,
            "temperature_celsius": temp,
            "weather": weather,
            "wind_speed_kmh": wind,
            "timezone": tz,
            "summary": summary,
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        logger.error("get_weather_by_city error: %s", exc)
        return json.dumps({"error": f"Unexpected error: {exc}"})


# ---------------------------------------------------------------------------
# Tool 2 — Book Recommendation
# ---------------------------------------------------------------------------

@mcp.tool()
def book_recommend(topic: str) -> str:
    """
    Recommend a book on a given topic using the Open Library search API.

    Args:
        topic: Subject or keyword to search for (e.g. "space exploration").

    Returns:
        JSON string with book title, author, and publication year.
    """
    # Normalize and correct common misspellings to improve search results
    def _normalize_topic(t: str) -> str:
        t = (t or "").lower().strip()
        # common typos
        corrections = {"mudder": "murder", "muder": "murder", "muder": "murder"}
        for a, b in corrections.items():
            t = re.sub(rf"\b{re.escape(a)}\b", b, t)
        # remove punctuation and collapse spaces
        t = re.sub(r"[^a-z0-9 ]+", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    url = "https://openlibrary.org/search.json"
    topic_norm = _normalize_topic(topic)

    # Try multiple query strategies to improve hit rate for fuzzy inputs
    attempts = [
        {"q": topic_norm, "limit": 10, "fields": "title,author_name,first_publish_year,first_sentence,subtitle"},
        {"q": topic, "limit": 10, "fields": "title,author_name,first_publish_year,first_sentence,subtitle"},
        {"q": topic_norm.replace(' ', '+'), "limit": 10, "fields": "title,author_name,first_publish_year,first_sentence,subtitle"},
    ]

    data = None
    for params in attempts:
        data = http_get(url, params=params)
        if data and data.get("docs"):
            break

    # As a last resort try subject search
    if (not data or not data.get("docs")) and topic_norm:
        params = {"subject": topic_norm, "limit": 10, "fields": "title,author_name,first_publish_year,first_sentence,subtitle"}
        data = http_get(url, params=params)

    if not data or not data.get("docs"):
        return json.dumps({"error": f"No books found for topic: '{topic}'"})

    docs = data["docs"]
    # Prefer results with an author and first_publish_year
    docs_sorted = sorted(docs, key=lambda d: (0 if d.get("author_name") else 1, 0 if d.get("first_publish_year") else 1))
    book = random.choice(docs_sorted[:min(10, len(docs_sorted))])

    title = book.get("title") or "Unknown Title"
    author = book.get("author_name", ["Unknown Author"])[0] if book.get("author_name") else "Unknown Author"
    year = book.get("first_publish_year", "Unknown")
    first_sentence = book.get("first_sentence") or book.get("subtitle") or ""

    result = {
        "title": title,
        "author": author,
        "year": year,
        "topic": topic,
        "summary": first_sentence,
    }

    logger.info("Book recommended for '%s': %s", topic, title)
    return json.dumps(result, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool 3 — Movie Recommendation
# ---------------------------------------------------------------------------

@mcp.tool()
def recommend_movie(genre: str) -> str:
    """
    Recommend a movie for a given genre.

    Uses TMDB API if TMDB_API_KEY is configured, otherwise falls back
    to the local movies.json dataset.

    Args:
        genre: Movie genre (e.g. "sci-fi", "comedy", "horror").

    Returns:
        JSON string with movie title, rating, overview, and year.
    """
    # Require TMDB API key for movie recommendations in production mode.
    if not config.TMDB_API_KEY:
        return json.dumps({
            "error": "TMDB API key is not configured. Set TMDB_API_KEY in config to enable movie recommendations."
        })

    result = _tmdb_recommend(genre)
    if result:
        return json.dumps(result)

    fallback = _fallback_movie(genre)
    if fallback:
        return json.dumps(fallback)

    return json.dumps({"error": "Could not fetch movie recommendations from TMDB right now."})


def _tmdb_recommend(genre: str) -> dict | None:
    """Fetch a movie recommendation from TMDB."""
    normalized = genre.strip().lower()

    # Map genre names to TMDB genre IDs or combined genre filters.
    genre_map = {
        "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
        "crime": 80, "documentary": 99, "drama": 18, "fantasy": 14,
        "horror": 27, "mystery": 9648, "romance": 10749,
        "sci-fi": 878, "science fiction": 878, "scifi": 878,
        "thriller": 53, "western": 37,
    }

    if "murder" in normalized and "mystery" in normalized:
        genre_id = "9648,80"
    elif "murder" in normalized:
        genre_id = "80"
    else:
        genre_id = genre_map.get(normalized)

    if not genre_id:
        if any(term in normalized for term in ["horror", "slasher", "zombie", "apocalypse", "supernatural", "ghost"]):
            genre_id = 27
        elif any(term in normalized for term in ["romcom", "romantic comedy"]):
            genre_id = 35
        elif any(term in normalized for term in ["sci", "science fiction", "scifi"]):
            genre_id = 878
        elif "action" in normalized:
            genre_id = 28
        elif "fantasy" in normalized:
            genre_id = 14
        elif "crime" in normalized:
            genre_id = 80
        elif "documentary" in normalized:
            genre_id = 99
        elif "drama" in normalized:
            genre_id = 18
        elif "thriller" in normalized:
            genre_id = 53

    if genre_id:
        url = "https://api.themoviedb.org/3/discover/movie"
        params = {
            "api_key": config.TMDB_API_KEY,
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "page": random.randint(1, 3),
        }
        if "mystery" in normalized:
            params["without_genres"] = 27
    else:
        logger.warning("TMDB: unknown genre '%s', falling back to popular movies.", genre)
        url = "https://api.themoviedb.org/3/movie/popular"
        params = {
            "api_key": config.TMDB_API_KEY,
            "page": random.randint(1, 3),
        }

    data = http_get(url, params=params)
    if not data or not data.get("results"):
        return None

    results = data["results"]
    if "murder" in normalized and "mystery" in normalized:
        filtered = [movie for movie in results if 27 not in movie.get("genre_ids", [])]
        if filtered:
            results = filtered

    movie = random.choice(results[:10])
    return {
        "title": movie.get("title", "Unknown"),
        "rating": movie.get("vote_average", 0),
        "overview": movie.get("overview", "No overview available."),
        "year": movie.get("release_date", "")[:4],
        "genre": genre,
        "source": "TMDB",
    }


def _fallback_movie(genre: str) -> dict | None:
    normalized = genre.strip().lower()
    if any(term in normalized for term in ["horror", "slasher", "zombie", "apocalypse", "supernatural", "ghost"]):
        bucket = _MOVIE_FALLBACKS.get("horror", [])
    elif any(term in normalized for term in ["sci", "science fiction", "scifi"]):
        bucket = _MOVIE_FALLBACKS.get("sci-fi", [])
    elif any(term in normalized for term in ["murder", "mystery", "detective", "whodunit", "crime"]):
        bucket = _MOVIE_FALLBACKS.get("mystery", [])
    else:
        bucket = _MOVIE_FALLBACKS.get("horror", [])

    if not bucket:
        return None

    movie = random.choice(bucket)
    return {
        "title": movie["title"],
        "rating": movie["rating"],
        "overview": movie["overview"],
        "year": movie["year"],
        "genre": genre,
        "source": movie["source"],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Reconfigure stdout to raw UTF-8 only when running as an MCP server.
    # This prevents Windows from mangling the JSON-RPC protocol bytes.
    # Must NOT be done at import time — it breaks pytest's stdout capture.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    logger.info("Starting ChillBot Info Server...")
    mcp.run(transport="stdio")
