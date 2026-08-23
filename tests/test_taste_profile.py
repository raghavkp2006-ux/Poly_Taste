"""
tests/test_taste_profile.py

Tests for the cross-module taste profile feature:
  - services/taste_profile.py :: compute_taste_profile, get_anime_boost_map
  - POST /anime/{mal_id}/like
  - DELETE /anime/{mal_id}/like
  - GET /taste-profile (requires auth)
  - GET /anime/{mal_id}/recommend?personalize=true

All external calls (Spotify API, DB) are mocked.
Style mirrors test_recommender.py + test_anime_extensions.py.
"""

from unittest.mock import MagicMock, patch
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared mock catalog data reused across fixtures
# ---------------------------------------------------------------------------

MOCK_ANIME_CATALOG = [
    {"mal_id": 1, "title": "Action Hero", "genres": ["Action", "Shonen"], "synopsis": "Fights"},
    {"mal_id": 2, "title": "Chill Vibes", "genres": ["Slice of Life", "Drama"], "synopsis": "Slow life"},
    {"mal_id": 3, "title": "Space Opera", "genres": ["Sci-Fi", "Mecha"], "synopsis": "Space"},
    {"mal_id": 4, "title": "Romance Tale", "genres": ["Romance", "Comedy"], "synopsis": "Love"},
    {"mal_id": 5, "title": "Sports Club", "genres": ["Sports", "Action"], "synopsis": "Athletics"},
]

# ---------------------------------------------------------------------------
# Module-level fixtures: patch anime + amazon catalog once for all tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_catalogs(monkeypatch):
    """Inject mock catalogs into both routers so no CSV/DB is needed."""
    import routers.anime as anime_router
    # --- Anime catalog ---
    monkeypatch.setattr(anime_router, "catalog", list(MOCK_ANIME_CATALOG))
    monkeypatch.setattr(anime_router, "mal_id_to_index",
                        {a["mal_id"]: i for i, a in enumerate(MOCK_ANIME_CATALOG)})

    # Inject a random latent tensor — shape (n_items, latent_dim=32) matching the real model.
    # We don't need realistic embeddings; we just need recommend_anime to not crash.
    import torch
    torch.manual_seed(42)
    fake_latent = torch.randn(len(MOCK_ANIME_CATALOG), 32)
    monkeypatch.setattr(anime_router, "latent_catalog", fake_latent)


@pytest.fixture(scope="module")
def client():
    from main import app
    return TestClient(app)


@pytest.fixture
def auth_override(client):
    """Inject a fixed user_id via dependency_overrides and clean up after test."""
    from main import app
    from services.auth import get_current_user_id

    app.dependency_overrides[get_current_user_id] = lambda: "user_test_42"
    yield "user_test_42"
    app.dependency_overrides.pop(get_current_user_id, None)


# ===========================================================================
# Tests: compute_taste_profile
# ===========================================================================

def test_compute_profile_spotify_only():
    """Spotify token provided, no DB likes → profile has Spotify genres."""
    from services.taste_profile import compute_taste_profile

    mock_artists = [
        {"id": "a1", "genres": ["rock"]},
        {"id": "a2", "genres": ["metal"]},
    ]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": mock_artists}

    with patch("services.taste_profile.requests.get", return_value=mock_resp), \
         patch("services.taste_profile.get_likes", return_value=[]):
        result = compute_taste_profile("user1", spotify_token="fake_token")

    assert "rock" in result["profile"] or "metal" in result["profile"]
    assert result["breakdown"]["anime"] == {}


def test_compute_profile_anime_likes_only():
    """No Spotify token, anime likes → anime genres in profile."""
    from services.taste_profile import compute_taste_profile

    anime_likes = [
        {"user_id": "user1", "module": "anime", "item_id": "1", "liked_at": 0},
        {"user_id": "user1", "module": "anime", "item_id": "3", "liked_at": 0},
    ]

    def mock_get_likes(user_id, module=None):
        if module == "anime":
            return anime_likes
        return []

    with patch("services.taste_profile.get_likes", side_effect=mock_get_likes):
        result = compute_taste_profile("user1", spotify_token=None)

    profile = result["profile"]
    # mal_id=1 → Action, Shonen; mal_id=3 → Sci-Fi, Mecha
    assert "action" in profile
    assert "sci-fi" in profile
    assert result["breakdown"]["spotify"] == {}


def test_compute_profile_combined():
    """Both sources active → genres from each module present and summed."""
    from services.taste_profile import compute_taste_profile

    anime_likes = [{"user_id": "u", "module": "anime", "item_id": "2", "liked_at": 0}]

    def mock_get_likes(user_id, module=None):
        if module == "anime":   return anime_likes
        return []

    mock_artists = [{"id": "a1", "genres": ["pop"]}]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": mock_artists}

    with patch("services.taste_profile.requests.get", return_value=mock_resp), \
         patch("services.taste_profile.get_likes", side_effect=mock_get_likes):
        result = compute_taste_profile("u", spotify_token="tok")

    profile = result["profile"]
    assert "pop" in profile
    assert "slice of life" in profile


def test_crosswalk_anime_present_for_rock_user():
    """A rock-genre Spotify user should get action/shonen in crosswalk_anime."""
    from services.taste_profile import compute_taste_profile

    mock_artists = [{"id": "a1", "genres": ["rock"]}]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": mock_artists}

    with patch("services.taste_profile.requests.get", return_value=mock_resp), \
         patch("services.taste_profile.get_likes", return_value=[]):
        result = compute_taste_profile("u", spotify_token="tok")

    crosswalk = result["crosswalk_anime"]
    assert "action" in crosswalk
    assert "shonen" in crosswalk


def test_get_anime_boost_map_returns_dict():
    """get_anime_boost_map returns a {genre: float} dict with no errors."""
    from services.taste_profile import get_anime_boost_map

    with patch("services.taste_profile.get_likes", return_value=[]):
        boost = get_anime_boost_map("user_x")

    assert isinstance(boost, dict)


# ===========================================================================
# Tests: POST/DELETE /anime/{mal_id}/like
# ===========================================================================

def test_anime_like_endpoint_201(client, auth_override):
    with patch("routers.anime.add_like") as mock_add:
        resp = client.post("/anime/1/like")
    assert resp.status_code == 201
    data = resp.json()
    assert data["liked"] is True
    assert data["mal_id"] == 1
    mock_add.assert_called_once_with("user_test_42", "anime", "1")


def test_anime_like_endpoint_404_unknown(client, auth_override):
    resp = client.post("/anime/99999/like")
    assert resp.status_code == 404


def test_anime_unlike_endpoint_200(client, auth_override):
    with patch("routers.anime.remove_like") as mock_rm:
        resp = client.delete("/anime/1/like")
    assert resp.status_code == 200
    data = resp.json()
    assert data["liked"] is False
    mock_rm.assert_called_once_with("user_test_42", "anime", "1")


def test_anime_like_requires_auth(client):
    """Like endpoint must return 401 when no session cookie present."""
    resp = client.post("/anime/1/like")
    assert resp.status_code == 401





# ===========================================================================
# Tests: GET /taste-profile
# ===========================================================================

def test_taste_profile_requires_auth(client):
    resp = client.get("/taste-profile")
    assert resp.status_code == 401


def test_taste_profile_authenticated_structure(client, auth_override):
    with patch("routers.taste.get_user", return_value=None), \
         patch("services.taste_profile.get_likes", return_value=[]):
        resp = client.get("/taste-profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "user_test_42"
    assert "profile" in data
    assert "breakdown" in data
    assert "crosswalk_anime" in data
    assert "spotify_connected" in data


# ===========================================================================
# Tests: GET /anime/{mal_id}/recommend?personalize=true
# ===========================================================================

def test_anime_recommend_no_personalize_unchanged(client):
    """?personalize=false (default) → no personalized_score field, existing behavior."""
    resp = client.get("/anime/1/recommend?n=2")
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    assert data["personalized"] is False
    # No personalized_score fields when not personalized
    for rec in data["recommendations"]:
        assert "personalized_score" not in rec


def test_anime_recommend_personalize_adds_scores(client, auth_override):
    """?personalize=true with a valid session → personalized_score added for genre-matching recs."""
    from services.auth import create_session_cookie

    boost_map = {"action": 5.0, "shonen": 3.0, "sports": 2.0}
    session_cookie = create_session_cookie("user_test_42")

    # Set cookie on client (preferred over deprecated per-request cookies)
    client.cookies.set("session", session_cookie)
    try:
        with patch("services.taste_profile.get_anime_boost_map", return_value=boost_map):
            resp = client.get("/anime/1/recommend?n=4&personalize=true")
    finally:
        client.cookies.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["personalized"] is True
    recs = data["recommendations"]

    # Every rec with a genre in boost_map must have personalized_score >= similarity_score
    for rec in recs:
        rec_genres_lower = [g.lower() for g in rec.get("genres", [])]
        has_boosted_genre = any(g in boost_map for g in rec_genres_lower)
        if has_boosted_genre:
            assert "personalized_score" in rec, f"Expected personalized_score on {rec['title']}"
            assert "genre_boost" in rec
            assert rec["personalized_score"] >= rec["similarity_score"]



def test_anime_recommend_personalize_reranks_action_higher(client, auth_override):
    """Rock/metal user → action/shonen anime should rank above drama/romance."""
    # Large boost for action/shonen (rock/metal Spotify taste)
    boost_map = {"action": 10.0, "shonen": 8.0, "slice of life": 0.0, "drama": 0.0}

    with patch("services.taste_profile.get_anime_boost_map", return_value=boost_map):
        resp = client.get("/anime/1/recommend?n=4&personalize=true")

    assert resp.status_code == 200
    recs = resp.json()["recommendations"]
    # Find action anime vs drama anime in results
    action_recs = [r for r in recs if "Action" in r.get("genres", [])]
    drama_recs = [r for r in recs if "Drama" in r.get("genres", []) and "Action" not in r.get("genres", [])]

    if action_recs and drama_recs:
        # Action rec must come before drama rec in sorted order
        action_positions = [recs.index(r) for r in action_recs]
        drama_positions = [recs.index(r) for r in drama_recs]
        assert min(action_positions) < min(drama_positions)
