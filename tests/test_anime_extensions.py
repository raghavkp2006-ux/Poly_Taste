"""
tests/test_anime_extensions.py

Tests for the four new Anime module endpoints:
  /anime/upcoming
  /anime/{mal_id}/reviews
  /anime/{mal_id}/videos
  /anime/{mal_id}/news

All external HTTP calls are mocked — no live network access is required.
Style mirrors tests/test_recommender.py (plain pytest functions, no class
fixtures, unittest.mock.patch for HTTP isolation).
"""

import json
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper fixtures / shared mock data
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_caches():
    """Ensure in-memory caches are clean before each test runs."""
    import services.anilist_client as client
    client._upcoming_cache = None
    client._upcoming_fetched_at = 0.0
    client._reviews_cache.clear()
    client._reviews_fetched_at.clear()

MOCK_ANILIST_UPCOMING = {
    "data": {
        "Page": {
            "media": [
                {
                    "id": 101,
                    "idMal": 9001,
                    "title": {"romaji": "Test Anime", "english": "Test Anime EN"},
                    "coverImage": {"medium": "https://example.com/cover.jpg"},
                    "genres": ["Action", "Adventure"],
                    "studios": {"nodes": [{"name": "Studio A"}]},
                    "description": "A test anime description.",
                    "startDate": {"year": 2025, "month": 10, "day": 1},
                }
            ]
        }
    }
}

MOCK_JIKAN_UPCOMING = {
    "data": [
        {
            "mal_id": 8888,
            "title": "Jikan Upcoming Anime",
            "images": {"jpg": {"image_url": "https://example.com/jikan.jpg"}},
            "genres": [{"name": "Sci-Fi"}],
            "studios": [{"name": "Studio B"}],
            "synopsis": "A Jikan upcoming synopsis.",
            "aired": {"from": "2025-10-01T00:00:00+00:00"},
        }
    ]
}

MOCK_ANILIST_REVIEWS = {
    "data": {
        "Media": {
            "id": 101,
            "title": {"romaji": "Test Anime", "english": "Test Anime EN"},
            "reviews": {
                "nodes": [
                    {
                        "id": 201,
                        "score": 90,
                        "summary": "An excellent series.",
                        "body": "This anime was absolutely fantastic in every way. " * 10,
                        "user": {"name": "reviewer42"},
                        "createdAt": 1700000000,
                    }
                ]
            },
        }
    }
}

MOCK_JIKAN_REVIEWS = {
    "data": [
        {
            "mal_id": 301,
            "scores": {"overall": 8},
            "user": {"username": "jikan_user"},
            "review": "Jikan review text here. " * 20,
            "date": "2024-01-01T00:00:00+00:00",
        }
    ]
}

MOCK_YOUTUBE_RESPONSE = {
    "items": [
        {
            "id": {"videoId": "abc123"},
            "snippet": {
                "title": "Test Anime Official Trailer",
                "channelTitle": "AnimeChannel",
                "thumbnails": {"medium": {"url": "https://i.ytimg.com/vi/abc123/mqdefault.jpg"}},
            },
        },
        {
            "id": {"videoId": "def456"},
            "snippet": {
                "title": "Test Anime Episode 1 Explained",
                "channelTitle": "AnimeExplains",
                "thumbnails": {"medium": {"url": "https://i.ytimg.com/vi/def456/mqdefault.jpg"}},
            },
        },
    ]
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_post_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    return mock


def _mock_get_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    return mock


# ===========================================================================
# 1. /anime/upcoming
# ===========================================================================

class TestUpcomingAniList:
    def test_upcoming_anilist_success(self):
        """AniList returns valid data → source=anilist, correct fields populated."""
        from services.anilist_client import fetch_upcoming_anime

        with patch("services.anilist_client.requests.post") as mock_post, \
             patch("services.anilist_client._cache_upcoming_local"):
            mock_post.return_value = _mock_post_response(MOCK_ANILIST_UPCOMING)
            result = fetch_upcoming_anime(per_page=5)

        assert result["source"] == "anilist"
        assert len(result["upcoming"]) == 1
        item = result["upcoming"][0]
        assert item["title"] == "Test Anime EN"
        assert item["mal_id"] == 9001
        assert item["genres"] == ["Action", "Adventure"]
        assert item["studios"] == ["Studio A"]
        assert item["start_date"] == "2025-10-01"

    def test_upcoming_anilist_fallback_to_jikan(self):
        """AniList POST fails → Jikan GET is tried and succeeds."""
        from services.anilist_client import fetch_upcoming_anime

        with patch("services.anilist_client.requests.post", side_effect=Exception("timeout")), \
             patch("services.anilist_client.requests.get") as mock_get, \
             patch("services.anilist_client._cache_upcoming_local"), \
             patch("services.anilist_client._load_upcoming_local", return_value=[]):
            mock_get.return_value = _mock_get_response(MOCK_JIKAN_UPCOMING)
            result = fetch_upcoming_anime(per_page=5)

        assert result["source"] == "jikan"
        assert len(result["upcoming"]) == 1
        assert result["upcoming"][0]["mal_id"] == 8888
        assert result["upcoming"][0]["title"] == "Jikan Upcoming Anime"

    def test_upcoming_both_fail_returns_empty(self):
        """Both AniList and Jikan fail, no local cache → returns empty list."""
        from services.anilist_client import fetch_upcoming_anime

        with patch("services.anilist_client.requests.post", side_effect=Exception("timeout")), \
             patch("services.anilist_client.requests.get", side_effect=Exception("timeout")), \
             patch("services.anilist_client._load_upcoming_local", return_value=[]):
            result = fetch_upcoming_anime(per_page=5)

        assert result["source"] == "none"
        assert result["upcoming"] == []

    def test_upcoming_anilist_empty_media_falls_back(self):
        """AniList returns 200 but empty media list → falls back to Jikan."""
        from services.anilist_client import fetch_upcoming_anime

        empty_response = {"data": {"Page": {"media": []}}}

        with patch("services.anilist_client.requests.post") as mock_post, \
             patch("services.anilist_client.requests.get") as mock_get, \
             patch("services.anilist_client._cache_upcoming_local"), \
             patch("services.anilist_client._load_upcoming_local", return_value=[]):
            mock_post.return_value = _mock_post_response(empty_response)
            mock_get.return_value = _mock_get_response(MOCK_JIKAN_UPCOMING)
            result = fetch_upcoming_anime(per_page=5)

        assert result["source"] == "jikan"

    def test_upcoming_cache_hit(self):
        """Cache hit skips network calls entirely."""
        from services.anilist_client import fetch_upcoming_anime
        import services.anilist_client as anilist_client
        import time

        # Seed the cache
        anilist_client._upcoming_cache = {"source": "anilist", "upcoming": [{"mock": "data"}]}
        anilist_client._upcoming_fetched_at = time.time()

        with patch("services.anilist_client.requests.post") as mock_post, \
             patch("services.anilist_client.requests.get") as mock_get:
            result = fetch_upcoming_anime(per_page=5)

        assert result["source"] == "anilist"
        assert result["upcoming"] == [{"mock": "data"}]
        mock_post.assert_not_called()
        mock_get.assert_not_called()

        # Clean up
        anilist_client._upcoming_cache = None

    def test_upcoming_cache_populated_from_jikan(self):
        """Cache is populated when Jikan fallback succeeds."""
        from services.anilist_client import fetch_upcoming_anime
        import services.anilist_client as anilist_client

        anilist_client._upcoming_cache = None

        with patch("services.anilist_client.requests.post", side_effect=Exception("error")), \
             patch("services.anilist_client.requests.get") as mock_get, \
             patch("services.anilist_client._cache_upcoming_local"):
            mock_get.return_value = _mock_get_response(MOCK_JIKAN_UPCOMING)
            result = fetch_upcoming_anime(per_page=5)

        assert result["source"] == "jikan"
        assert anilist_client._upcoming_cache is not None
        assert anilist_client._upcoming_cache["source"] == "jikan"

        # Clean up
        anilist_client._upcoming_cache = None

    def test_upcoming_stale_cache_served_when_both_fail(self):
        """Stale cache is served if both sources fail."""
        from services.anilist_client import fetch_upcoming_anime
        import services.anilist_client as anilist_client
        import time

        # Seed the cache with expired timestamp
        anilist_client._upcoming_cache = {"source": "stale", "upcoming": [{"mock": "stale_data"}]}
        anilist_client._upcoming_fetched_at = time.time() - 20000  # Older than TTL

        with patch("services.anilist_client.requests.post", side_effect=Exception("error")), \
             patch("services.anilist_client.requests.get", side_effect=Exception("error")):
            result = fetch_upcoming_anime(per_page=5)

        assert result["source"] == "stale"
        assert result["upcoming"] == [{"mock": "stale_data"}]

        # Clean up
        anilist_client._upcoming_cache = None


# ===========================================================================
# 2. /anime/{mal_id}/reviews
# ===========================================================================

class TestReviews:
    def test_reviews_anilist_success(self):
        """AniList returns valid reviews → source=anilist, correct shape."""
        from services.anilist_client import fetch_reviews_by_mal_id

        with patch("services.anilist_client.requests.post") as mock_post:
            mock_post.return_value = _mock_post_response(MOCK_ANILIST_REVIEWS)
            result = fetch_reviews_by_mal_id(mal_id=1, per_page=5)

        assert result["source"] == "anilist"
        assert result["mal_id"] == 1
        assert result["title"] == "Test Anime EN"
        assert len(result["reviews"]) == 1

        review = result["reviews"][0]
        assert review["score"] == 90
        assert review["username"] == "reviewer42"
        assert review["summary"] == "An excellent series."
        # Snippet should be at most 401 chars (400 + ellipsis)
        assert len(review["snippet"]) <= 401
        assert review["created_at"] is not None

    def test_reviews_snippet_truncation(self):
        """Body longer than 400 chars should be truncated with ellipsis."""
        from services.anilist_client import fetch_reviews_by_mal_id

        long_body = "x" * 600
        data = {
            "data": {
                "Media": {
                    "id": 1,
                    "title": {"romaji": "T", "english": None},
                    "reviews": {
                        "nodes": [
                            {
                                "id": 1,
                                "score": 70,
                                "summary": "short",
                                "body": long_body,
                                "user": {"name": "u"},
                                "createdAt": 1700000000,
                            }
                        ]
                    },
                }
            }
        }
        with patch("services.anilist_client.requests.post") as mock_post:
            mock_post.return_value = _mock_post_response(data)
            result = fetch_reviews_by_mal_id(mal_id=1)

        snippet = result["reviews"][0]["snippet"]
        assert snippet.endswith("…")
        assert len(snippet) == 401  # 400 chars + "…"

    def test_reviews_anilist_fallback_to_jikan(self):
        """AniList returns no Media → Jikan fallback is used."""
        from services.anilist_client import fetch_reviews_by_mal_id

        empty_response = {"data": {"Media": None}}

        with patch("services.anilist_client.requests.post") as mock_post, \
             patch("services.anilist_client.requests.get") as mock_get:
            mock_post.return_value = _mock_post_response(empty_response)
            mock_get.return_value = _mock_get_response(MOCK_JIKAN_REVIEWS)
            result = fetch_reviews_by_mal_id(mal_id=1)

        assert result["source"] == "jikan"
        assert result["reviews"][0]["username"] == "jikan_user"
        assert result["reviews"][0]["score"] == 8

    def test_reviews_anilist_http_error_fallback(self):
        """AniList HTTP error → Jikan fallback."""
        from services.anilist_client import fetch_reviews_by_mal_id

        with patch("services.anilist_client.requests.post") as mock_post, \
             patch("services.anilist_client.requests.get") as mock_get:
            mock_post.return_value = _mock_post_response({}, status_code=500)
            mock_get.return_value = _mock_get_response(MOCK_JIKAN_REVIEWS)
            result = fetch_reviews_by_mal_id(mal_id=1)

        assert result["source"] == "jikan"

    def test_reviews_cache_hit(self):
        """Cache hit skips network calls entirely."""
        from services.anilist_client import fetch_reviews_by_mal_id
        import services.anilist_client as anilist_client
        import time

        anilist_client._reviews_cache[999] = {"source": "anilist", "reviews": [{"mock": "data"}]}
        anilist_client._reviews_fetched_at[999] = time.time()

        with patch("services.anilist_client.requests.post") as mock_post, \
             patch("services.anilist_client.requests.get") as mock_get:
            result = fetch_reviews_by_mal_id(mal_id=999, per_page=5)

        assert result["source"] == "anilist"
        assert result["reviews"] == [{"mock": "data"}]
        mock_post.assert_not_called()
        mock_get.assert_not_called()

        # Clean up
        del anilist_client._reviews_cache[999]

    def test_reviews_cache_populated_from_jikan(self):
        """Cache is populated when Jikan fallback succeeds."""
        from services.anilist_client import fetch_reviews_by_mal_id
        import services.anilist_client as anilist_client

        if 998 in anilist_client._reviews_cache:
            del anilist_client._reviews_cache[998]

        with patch("services.anilist_client.requests.post", side_effect=Exception("error")), \
             patch("services.anilist_client.requests.get") as mock_get:
            mock_get.return_value = _mock_get_response(MOCK_JIKAN_REVIEWS)
            result = fetch_reviews_by_mal_id(mal_id=998, per_page=5)

        assert result["source"] == "jikan"
        assert 998 in anilist_client._reviews_cache
        assert anilist_client._reviews_cache[998]["source"] == "jikan"

        # Clean up
        del anilist_client._reviews_cache[998]

    def test_reviews_stale_cache_served_when_both_fail(self):
        """Stale cache is served if both sources fail."""
        from services.anilist_client import fetch_reviews_by_mal_id
        import services.anilist_client as anilist_client
        import time

        anilist_client._reviews_cache[997] = {"source": "stale", "reviews": [{"mock": "stale_data"}]}
        anilist_client._reviews_fetched_at[997] = time.time() - 10000  # Older than TTL

        with patch("services.anilist_client.requests.post", side_effect=Exception("error")), \
             patch("services.anilist_client.requests.get", side_effect=Exception("error")):
            result = fetch_reviews_by_mal_id(mal_id=997, per_page=5)

        assert result["source"] == "stale"
        assert result["reviews"] == [{"mock": "stale_data"}]

        # Clean up
        if 997 in anilist_client._reviews_cache:
            del anilist_client._reviews_cache[997]


# ===========================================================================
# 3. /anime/{mal_id}/videos
# ===========================================================================

class TestVideos:
    """
    The videos endpoint lives in routers/anime.py and calls requests.get
    directly.  We test the route logic via the service layer by importing
    the handler and mocking the catalog + YouTube API call.
    """

    def _make_catalog_patch(self, mal_id: int = 1, title: str = "Test Anime"):
        """Return patches that fake a one-entry in-memory catalog."""
        return {
            "catalog": [{"mal_id": mal_id, "title": title, "genres": ["Action"]}],
            "mal_id_to_index": {mal_id: 0},
        }

    def test_videos_success(self):
        """YouTube returns 2 items → 2 video dicts with correct fields."""
        import routers.anime as anime_router

        catalog_data = self._make_catalog_patch()

        with patch.object(anime_router, "catalog", catalog_data["catalog"]), \
             patch.object(anime_router, "mal_id_to_index", catalog_data["mal_id_to_index"]), \
             patch.object(anime_router, "YOUTUBE_API_KEY", "fake-key"), \
             patch("routers.anime.requests.get") as mock_get:
            mock_get.return_value = _mock_get_response(MOCK_YOUTUBE_RESPONSE)
            result = anime_router.get_anime_videos(mal_id=1, max_results=5)

        assert len(result["videos"]) == 2
        assert result["videos"][0]["video_id"] == "abc123"
        assert result["videos"][0]["channel"] == "AnimeChannel"
        assert result["videos"][1]["video_id"] == "def456"
        assert result["anime_title"] == "Test Anime"
        assert "explained OR trailer OR PV" in result["query"]

    def test_videos_no_api_key_raises_503(self):
        """Missing YOUTUBE_API_KEY → HTTPException 503."""
        import routers.anime as anime_router
        from fastapi import HTTPException

        catalog_data = self._make_catalog_patch()

        with patch.object(anime_router, "catalog", catalog_data["catalog"]), \
             patch.object(anime_router, "mal_id_to_index", catalog_data["mal_id_to_index"]), \
             patch.object(anime_router, "YOUTUBE_API_KEY", None):
            with pytest.raises(HTTPException) as exc_info:
                anime_router.get_anime_videos(mal_id=1, max_results=5)

        assert exc_info.value.status_code == 503
        assert "YOUTUBE_API_KEY" in exc_info.value.detail

    def test_videos_unknown_mal_id_raises_404(self):
        """Unknown mal_id → HTTPException 404 before calling YouTube."""
        import routers.anime as anime_router
        from fastapi import HTTPException

        with patch.object(anime_router, "catalog", []), \
             patch.object(anime_router, "mal_id_to_index", {}), \
             patch.object(anime_router, "YOUTUBE_API_KEY", "fake-key"):
            with pytest.raises(HTTPException) as exc_info:
                anime_router.get_anime_videos(mal_id=9999, max_results=5)

        assert exc_info.value.status_code == 404

    def test_videos_youtube_api_error_raises_503(self):
        """YouTube returns non-200 → HTTPException with YouTube status code."""
        import routers.anime as anime_router
        from fastapi import HTTPException

        catalog_data = self._make_catalog_patch()

        with patch.object(anime_router, "catalog", catalog_data["catalog"]), \
             patch.object(anime_router, "mal_id_to_index", catalog_data["mal_id_to_index"]), \
             patch.object(anime_router, "YOUTUBE_API_KEY", "fake-key"), \
             patch("routers.anime.requests.get") as mock_get:
            mock_get.return_value = _mock_get_response({"error": {"message": "quota exceeded"}}, status_code=403)
            with pytest.raises(HTTPException) as exc_info:
                anime_router.get_anime_videos(mal_id=1, max_results=5)

        assert exc_info.value.status_code == 403


# ===========================================================================
# 4. /anime/{mal_id}/news
# ===========================================================================

class TestNews:
    def _make_feed(self, entries: list) -> MagicMock:
        """Build a fake feedparser result object."""
        mock_feed = MagicMock()
        mock_feed.entries = entries
        return mock_feed

    def _make_entry(self, title: str, summary: str, link: str = "https://ann.com/1", published: str = "Fri, 18 Jul 2025 10:00:00 +0000") -> dict:
        return {
            "title": title,
            "summary": summary,
            "link": link,
            "published": published,
        }

    def test_news_matching_by_title(self):
        """Entries whose title contains the anime name are returned."""
        import routers.anime as anime_router

        catalog = [{"mal_id": 1, "title": "Cowboy Bebop", "genres": []}]
        mal_id_to_index = {1: 0}

        entries = [
            self._make_entry("Cowboy Bebop Remake Announced", "Details about the remake."),
            self._make_entry("One Piece New Arc", "Something about One Piece."),
            self._make_entry("Cowboy Bebop Blu-ray Release", "The Blu-ray set ships in October."),
        ]
        fake_feed = self._make_feed(entries)

        with patch.object(anime_router, "catalog", catalog), \
             patch.object(anime_router, "mal_id_to_index", mal_id_to_index), \
             patch.object(anime_router, "_ann_feed", fake_feed):
            result = anime_router.get_anime_news(mal_id=1)

        assert result["anime_title"] == "Cowboy Bebop"
        assert len(result["articles"]) == 2
        assert all("Cowboy Bebop" in a["title"] for a in result["articles"])

    def test_news_matching_by_summary(self):
        """Entries whose summary contains the anime name are also returned."""
        import routers.anime as anime_router

        catalog = [{"mal_id": 2, "title": "Naruto", "genres": []}]
        mal_id_to_index = {2: 0}

        entries = [
            self._make_entry(
                "Weekly Anime Roundup",
                "This week features Naruto Shippuden, One Piece, and Bleach.",
            ),
            self._make_entry("Dragon Ball News", "Goku returns in a new arc."),
        ]
        fake_feed = self._make_feed(entries)

        with patch.object(anime_router, "catalog", catalog), \
             patch.object(anime_router, "mal_id_to_index", mal_id_to_index), \
             patch.object(anime_router, "_ann_feed", fake_feed):
            result = anime_router.get_anime_news(mal_id=2)

        assert len(result["articles"]) == 1
        assert "Weekly Anime Roundup" in result["articles"][0]["title"]

    def test_news_no_match_returns_empty(self):
        """No matching entries → empty articles list."""
        import routers.anime as anime_router

        catalog = [{"mal_id": 3, "title": "Ghost in the Shell", "genres": []}]
        mal_id_to_index = {3: 0}

        entries = [
            self._make_entry("Dragon Ball News", "Goku fights again."),
            self._make_entry("One Piece Chapter 1100", "Luffy reaches the island."),
        ]
        fake_feed = self._make_feed(entries)

        with patch.object(anime_router, "catalog", catalog), \
             patch.object(anime_router, "mal_id_to_index", mal_id_to_index), \
             patch.object(anime_router, "_ann_feed", fake_feed):
            result = anime_router.get_anime_news(mal_id=3)

        assert result["articles"] == []

    def test_news_summary_truncated_to_300_chars(self):
        """Summary longer than 300 chars should be truncated with ellipsis."""
        import routers.anime as anime_router

        catalog = [{"mal_id": 4, "title": "Akira", "genres": []}]
        mal_id_to_index = {4: 0}
        long_summary = "Akira " + "x" * 400

        entries = [self._make_entry("Akira 4K Remaster", long_summary)]
        fake_feed = self._make_feed(entries)

        with patch.object(anime_router, "catalog", catalog), \
             patch.object(anime_router, "mal_id_to_index", mal_id_to_index), \
             patch.object(anime_router, "_ann_feed", fake_feed):
            result = anime_router.get_anime_news(mal_id=4)

        summary = result["articles"][0]["summary"]
        assert summary.endswith("…")
        assert len(summary) == 301  # 300 chars + "…"

    def test_news_unknown_mal_id_raises_404(self):
        """Unknown mal_id → HTTPException 404."""
        import routers.anime as anime_router
        from fastapi import HTTPException

        with patch.object(anime_router, "catalog", []), \
             patch.object(anime_router, "mal_id_to_index", {}):
            with pytest.raises(HTTPException) as exc_info:
                anime_router.get_anime_news(mal_id=9999)

        assert exc_info.value.status_code == 404
