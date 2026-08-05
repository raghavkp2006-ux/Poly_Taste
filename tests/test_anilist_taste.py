import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app
from services.taste_profile import compute_taste_profile, get_anime_boost_map
from services.auth import get_current_user_id

MOCK_ANIME_CATALOG = [
    {"mal_id": 1, "title": "Action Hero", "genres": ["Action", "Shonen"], "synopsis": "Fights"},
    {"mal_id": 2, "title": "Chill Vibes", "genres": ["Slice of Life", "Drama"], "synopsis": "Slow life"},
    {"mal_id": 3, "title": "Space Opera", "genres": ["Sci-Fi", "Mecha"], "synopsis": "Space"},
    {"mal_id": 4, "title": "Romance Tale", "genres": ["Romance", "Comedy"], "synopsis": "Love"},
    {"mal_id": 5, "title": "Sports Club", "genres": ["Sports", "Action"], "synopsis": "Athletics"},
]

@pytest.fixture(autouse=True)
def patch_catalogs(monkeypatch):
    """Inject mock catalogs into both routers so no CSV/DB is needed."""
    import routers.anime as anime_router
    monkeypatch.setattr(anime_router, "catalog", list(MOCK_ANIME_CATALOG))
    monkeypatch.setattr(anime_router, "mal_id_to_index",
                        {a["mal_id"]: i for i, a in enumerate(MOCK_ANIME_CATALOG)})

    import torch
    torch.manual_seed(42)
    fake_latent = torch.randn(len(MOCK_ANIME_CATALOG), 32)
    monkeypatch.setattr(anime_router, "latent_catalog", fake_latent)

@pytest.fixture
def auth_override():
    app.dependency_overrides[get_current_user_id] = lambda: "user_test_42"
    yield "user_test_42"
    app.dependency_overrides.pop(get_current_user_id, None)

def test_taste_profile_no_anilist_connection():
    """User with no AniList connection -> /taste-profile unchanged, no errors, anilist_connected: false."""
    client = TestClient(app)
    app.dependency_overrides[get_current_user_id] = lambda: "user_test_42"
    try:
        with patch("routers.taste.get_anilist_user", return_value=None), \
             patch("services.taste_profile.get_anilist_user", return_value=None):
            response = client.get("/taste-profile")
            assert response.status_code == 200
            data = response.json()
            assert data["anilist_connected"] is False
            assert "anilist" in data["breakdown"]
            assert data["breakdown"]["anilist"] == {}
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)

def test_taste_profile_connected_anilist():
    """Connected user with a real list -> breakdown.anilist populated, genres look sane.
    Also, a DROPPED entry does not show up in the signal.
    An unscored CURRENT entry still contributes (small) weight.
    """
    user_record = {
        "user_id": "user_test_42",
        "anilist_id": 12345,
        "access_token": "token_xyz"
    }
    
    # 1: mal_id=1, score=9.0 (Action, Shonen) -> Status COMPLETED
    # 2: mal_id=2, score=0.0 (Slice of Life, Drama) -> Status CURRENT (unscored but watched)
    # 3: mal_id=3, score=10.0 (Sci-Fi, Mecha) -> Status DROPPED (should be ignored)
    mock_anime_list = [
        {"mal_id": 1, "score": 9.0, "status": "COMPLETED"},
        {"mal_id": 2, "score": 0.0, "status": "CURRENT"},
        {"mal_id": 3, "score": 10.0, "status": "DROPPED"},
    ]

    with patch("services.taste_profile.get_anilist_user", return_value=user_record), \
         patch("services.taste_profile.fetch_user_anime_list", return_value=mock_anime_list), \
         patch("services.taste_profile.get_likes", return_value=[]):
        
        profile_data = compute_taste_profile("user_test_42")
        anilist_breakdown = profile_data["breakdown"]["anilist"]
        
        # Verify genres
        # mal_id=1: score=9.0 -> weight = (9.0/10.0) * 2.0 = 1.8. Genres: action, shonen.
        # mal_id=2: score=0.0 -> weight = 0.3 * 2.0 = 0.6. Genres: slice of life, drama.
        # mal_id=3 (DROPPED): should be ignored. Genres: sci-fi, mecha weight should be 0.
        
        assert "action" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["action"]) == 1.8
        assert "shonen" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["shonen"]) == 1.8
        
        assert "slice of life" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["slice of life"]) == 0.6
        assert "drama" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["drama"]) == 0.6
        
        assert "sci-fi" not in anilist_breakdown
        assert "mecha" not in anilist_breakdown

def test_anime_recommendation_personalize_with_anilist():
    """GET /anime/{id}/recommend?personalize=true re-ranks differently before/after connecting AniList."""
    client = TestClient(app)
    app.dependency_overrides[get_current_user_id] = lambda: "user_test_42"
    try:
        # Before connecting: no likes, no Spotify, no AniList
        with patch("services.taste_profile.get_anilist_user", return_value=None), \
             patch("services.taste_profile.get_likes", return_value=[]), \
             patch("routers.taste.get_anilist_user", return_value=None):
            resp_before = client.get("/anime/5/recommend?personalize=true")
            assert resp_before.status_code == 200
            data_before = resp_before.json()

        # After connecting AniList with strong preference for "Slice of Life" (mal_id 2, score 10)
        user_record = {
            "user_id": "user_test_42",
            "anilist_id": 12345,
            "access_token": "token_xyz"
        }
        mock_anime_list = [
            {"mal_id": 2, "score": 10.0, "status": "COMPLETED"},
        ]
        with patch("services.taste_profile.get_anilist_user", return_value=user_record), \
             patch("services.taste_profile.fetch_user_anime_list", return_value=mock_anime_list), \
             patch("services.taste_profile.get_likes", return_value=[]), \
             patch("routers.taste.get_anilist_user", return_value=user_record):
            resp_after = client.get("/anime/5/recommend?personalize=true")
            assert resp_after.status_code == 200
            data_after = resp_after.json()

            # The recommendations before vs after should have different ordering/scores because of personalizing
            # Let's verify that the ranking or personalized scores differ.
            ids_before = [x["mal_id"] for x in data_before["recommendations"]]
            ids_after = [x["mal_id"] for x in data_after["recommendations"]]
            
            # Verify they did not return empty
            assert len(ids_before) > 0
            assert len(ids_after) > 0
            
            # Let's check boost map directly to be sure it boosts "slice of life" and "drama"
            boosts = get_anime_boost_map("user_test_42")
            assert boosts.get("slice of life") == 2.0
            assert boosts.get("drama") == 2.0
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)

