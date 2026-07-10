"""
test_books.py — Unit tests for the book_recommend tool.
"""

import json
from unittest.mock import patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servers.info_server import book_recommend


MOCK_OPEN_LIBRARY_RESPONSE = {
    "docs": [
        {"title": "A Brief History of Time", "author_name": ["Stephen Hawking"], "first_publish_year": 1988},
        {"title": "The Elegant Universe", "author_name": ["Brian Greene"], "first_publish_year": 1999},
        {"title": "Cosmos", "author_name": ["Carl Sagan"], "first_publish_year": 1980},
    ]
}


class TestBookRecommend:

    @patch("servers.info_server.http_get", return_value=MOCK_OPEN_LIBRARY_RESPONSE)
    def test_returns_valid_json(self, mock_get):
        result = book_recommend("space")
        data = json.loads(result)
        assert "title" in data
        assert "author" in data
        assert "year" in data

    @patch("servers.info_server.http_get", return_value=MOCK_OPEN_LIBRARY_RESPONSE)
    def test_title_is_string(self, mock_get):
        result = book_recommend("physics")
        data = json.loads(result)
        assert isinstance(data["title"], str)
        assert len(data["title"]) > 0

    @patch("servers.info_server.http_get", return_value=MOCK_OPEN_LIBRARY_RESPONSE)
    def test_author_is_string(self, mock_get):
        result = book_recommend("science")
        data = json.loads(result)
        assert isinstance(data["author"], str)

    @patch("servers.info_server.http_get", return_value={"docs": []})
    def test_no_results_returns_error(self, mock_get):
        result = book_recommend("xyznonexistenttopic123")
        data = json.loads(result)
        assert "error" in data

    @patch("servers.info_server.http_get", return_value=None)
    def test_api_failure_returns_error(self, mock_get):
        result = book_recommend("anything")
        data = json.loads(result)
        assert "error" in data

    @patch("servers.info_server.http_get", return_value=MOCK_OPEN_LIBRARY_RESPONSE)
    def test_topic_echoed_in_response(self, mock_get):
        result = book_recommend("astronomy")
        data = json.loads(result)
        assert data["topic"] == "astronomy"
