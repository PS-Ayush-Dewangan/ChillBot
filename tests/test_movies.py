"""
test_movies.py — Unit tests for the recommend_movie tool.
"""

import json
from unittest.mock import patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servers.info_server import recommend_movie


MOCK_TMDB_RESPONSE = {
    "results": [
        {
            "title": "Interstellar",
            "vote_average": 8.6,
            "overview": "A team of explorers travel through a wormhole.",
            "release_date": "2014-11-07",
        }
    ]
}


class TestRecommendMovie:

    @patch("servers.info_server.config")
    @patch("servers.info_server.http_get", return_value=MOCK_TMDB_RESPONSE)
    def test_tmdb_returns_valid_json(self, mock_get, mock_config):
        mock_config.TMDB_API_KEY = "fake_key"
        result = recommend_movie("sci-fi")
        data = json.loads(result)
        assert "title" in data
        assert "rating" in data
        assert "overview" in data
        assert "year" in data

    def test_missing_api_key_returns_error(self):
        with patch("servers.info_server.config") as mock_config:
            mock_config.TMDB_API_KEY = ""
            result = recommend_movie("sci-fi")
        data = json.loads(result)
        assert data["error"].startswith("TMDB API key")

    @patch("servers.info_server.config")
    @patch("servers.info_server.http_get", return_value=None)
    def test_tmdb_failure_uses_fallback(self, mock_get, mock_config):
        mock_config.TMDB_API_KEY = "fake_key"
        result = recommend_movie("action")
        data = json.loads(result)
        assert data["source"] == "fallback"
        assert data["title"] in {"The Conjuring", "A Quiet Place", "Get Out"}

    def test_murder_mystery_uses_combined_genres(self):
        with patch("servers.info_server.http_get") as mock_get, \
             patch("servers.info_server.config") as mock_config, \
             patch("servers.info_server.random.choice", side_effect=lambda seq: seq[0]):
            mock_config.TMDB_API_KEY = "fake_key"
            mock_get.return_value = {
                "results": [
                    {
                        "title": "Knives Out",
                        "vote_average": 7.9,
                        "overview": "A detective investigates a rich family's secrets.",
                        "release_date": "2019-11-27",
                        "genre_ids": [9648, 80],
                    }
                ]
            }

            result = recommend_movie("murder mystery")
            data = json.loads(result)
            assert data["title"] == "Knives Out"
            assert mock_get.call_args.kwargs["params"]["with_genres"] == "9648,80"
