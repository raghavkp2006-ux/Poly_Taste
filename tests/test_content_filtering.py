"""
tests/test_content_filtering.py

Tests for adult content filtering across Anime data sources (AniList, Jikan, Kitsu).
Ensures that entries with isAdult, rating == Rx, or ageRating == R18 are excluded.
"""

from typing import Any, Dict

import pytest

from services.anilist_client import _parse_upcoming_anilist, _fetch_upcoming_jikan
from services.jikan_client import fetch_top_anime

# ---------------------------------------------------------------------------
# AniList
# ---------------------------------------------------------------------------

def test_anilist_filters_isAdult():
    """Verify that _parse_upcoming_anilist ignores items where isAdult == True."""
    mock_data = {
        "data": {
            "Page": {
                "media": [
                    {
                        "id": 1,
                        "title": {"english": "Normal Anime"},
                        "isAdult": False
                    },
                    {
                        "id": 2,
                        "title": {"english": "Adult Anime"},
                        "isAdult": True
                    },
                    {
                        "id": 3,
                        "title": {"english": "Missing isAdult Field"},
                        # isAdult is implicitly falsy (None)
                    }
                ]
            }
        }
    }
    
    results = _parse_upcoming_anilist(mock_data)
    
    assert len(results) == 2
    assert results[0]["id"] == 1
    assert results[1]["id"] == 3

# ---------------------------------------------------------------------------
# Jikan
# ---------------------------------------------------------------------------

def test_jikan_filters_adult_ratings(mocker):
    """Verify that Jikan upcoming fetcher ignores Rx and R+ ratings."""
    mock_data = {
        "data": [
            {
                "mal_id": 1,
                "title": "Normal Anime",
                "rating": "PG-13 - Teens 13 or older"
            },
            {
                "mal_id": 2,
                "title": "Hentai Anime",
                "rating": "Rx - Hentai"
            },
            {
                "mal_id": 3,
                "title": "Mild Nudity Anime",
                "rating": "R+ - Mild Nudity"
            },
            {
                "mal_id": 4,
                "title": "Unknown Rating Anime",
                "rating": None
            }
        ]
    }
    
    # Mock requests.get to return this mock data
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_data
    mocker.patch("services.anilist_client.requests.get", return_value=mock_response)
    
    results = _fetch_upcoming_jikan(limit=10)
    
    assert len(results) == 2
    assert results[0]["mal_id"] == 1
    assert results[1]["mal_id"] == 4

# ---------------------------------------------------------------------------
# Kitsu (Jikan fallback script)
# ---------------------------------------------------------------------------

def test_kitsu_filters_age_rating(mocker):
    """Verify that Kitsu catalog fetcher ignores R18 ageRating."""
    mock_data = {
        "data": [
            {
                "id": "1",
                "attributes": {
                    "canonicalTitle": "Normal Anime",
                    "ageRating": "PG"
                },
                "relationships": {}
            },
            {
                "id": "2",
                "attributes": {
                    "canonicalTitle": "Adult Anime",
                    "ageRating": "R18"
                },
                "relationships": {}
            },
            {
                "id": "3",
                "attributes": {
                    "canonicalTitle": "Unknown Rating Anime",
                    # no ageRating
                },
                "relationships": {}
            }
        ],
        "included": []
    }
    
    # Mock requests.get to return this mock data
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_data
    mocker.patch("services.jikan_client.requests.get", return_value=mock_response)
    
    # Run fetch_top_anime, which loops page 0..4, so we mock it to break or return empty after page 0
    # Actually, the simplest way is to make the mock return the mock_data on the first call,
    # and then return a 404 to break the loop.
    def mock_get(url, params=None, timeout=None):
        if params and params.get("page[offset]") == 0:
            return mock_response
        else:
            resp = mocker.Mock()
            resp.status_code = 404
            return resp

    mocker.patch("services.jikan_client.requests.get", side_effect=mock_get)
    
    # Patch sleep to make it fast
    mocker.patch("services.jikan_client.time.sleep")
    
    results = fetch_top_anime()
    
    assert len(results) == 2
    assert results[0]["mal_id"] == 1
    assert results[1]["mal_id"] == 3
