"""
test_weather.py — Unit tests for the get_weather tool.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on the path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from servers.info_server import get_weather


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_WEATHER_RESPONSE = {
    "current_weather": {
        "temperature": 18.5,
        "windspeed": 12.3,
        "weathercode": 1,
    },
    "timezone": "Europe/London",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetWeather:

    @patch("servers.info_server.http_get", return_value=MOCK_WEATHER_RESPONSE)
    def test_returns_valid_json(self, mock_get):
        result = get_weather(51.5, -0.1)
        data = json.loads(result)
        assert "temperature_celsius" in data
        assert "weather" in data
        assert "wind_speed_kmh" in data
        assert "timezone" in data

    @patch("servers.info_server.http_get", return_value=MOCK_WEATHER_RESPONSE)
    def test_correct_temperature(self, mock_get):
        result = get_weather(51.5, -0.1)
        data = json.loads(result)
        assert data["temperature_celsius"] == 18.5

    @patch("servers.info_server.http_get", return_value=MOCK_WEATHER_RESPONSE)
    def test_weather_description_decoded(self, mock_get):
        result = get_weather(51.5, -0.1)
        data = json.loads(result)
        assert data["weather"] == "Mainly clear"

    @patch("servers.info_server.http_get", return_value=MOCK_WEATHER_RESPONSE)
    def test_timezone_returned(self, mock_get):
        result = get_weather(51.5, -0.1)
        data = json.loads(result)
        assert data["timezone"] == "Europe/London"

    @patch("servers.info_server.http_get", return_value=None)
    def test_graceful_fallback_on_api_failure(self, mock_get):
        result = get_weather(0.0, 0.0)
        data = json.loads(result)
        assert "error" in data

    @patch("servers.info_server.http_get", return_value=MOCK_WEATHER_RESPONSE)
    def test_coordinates_echoed(self, mock_get):
        result = get_weather(48.85, 2.35)
        data = json.loads(result)
        assert data["latitude"] == 48.85
        assert data["longitude"] == 2.35


class TestGetWeatherByCity:

    @patch("servers.info_server.requests.get")
    @patch("servers.info_server.get_weather", return_value=json.dumps({
        "temperature_celsius": 29.4,
        "weather": "Clear sky",
        "wind_speed_kmh": 8.1,
        "timezone": "Asia/Kolkata",
        "location_name": "Vadodara",
        "latitude": 22.3072,
        "longitude": 73.1812,
    }))
    def test_get_weather_by_city_parses_natural_language(self, mock_get_weather, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "lat": "22.3072",
                "lon": "73.1812",
                "address": {"city": "Vadodara", "state": "Gujarat", "country": "India"},
            }
        ]
        mock_requests_get.return_value = mock_response

        from servers.info_server import get_weather_by_city
        result = get_weather_by_city("tell me weather of vadodara,gujarat,india")
        data = json.loads(result)

        assert "Vadodara" in data["location"]
        assert data["temperature_celsius"] == 29.4
        assert data["timezone"] == "Asia/Kolkata"
