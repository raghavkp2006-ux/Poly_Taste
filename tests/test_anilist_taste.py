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
    monkeypatch.setattr(anime_router, "anime_data_map",
                        {str(a["mal_id"]): a for a in MOCK_ANIME_CATALOG})

    import numpy as np
    np.random.seed(42)
    fake_latent = np.random.randn(len(MOCK_ANIME_CATALOG), 32).astype(np.float32)
    monkeypatch.setattr(anime_router, "latent_matrix", fake_latent)
    monkeypatch.setattr(anime_router, "latent_ids", [str(a["mal_id"]) for a in MOCK_ANIME_CATALOG])

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
    """Connected user with a real list -> breakdown.anilist populated.
    Rated entries get score-proportional weight; unscored entries (score == 0)
    get a reduced default weight (0.5 * _ANILIST_WEIGHT = 1.0).
    DROPPED entries are ignored.
    """
    user_record = {
        "user_id": "user_test_42",
        "anilist_id": 12345,
        "access_token": "token_xyz"
    }
    
    # 1: mal_id=1, score=9.0 (Action, Shonen) -> Status COMPLETED -> contributes
    # 2: mal_id=2, score=0.0 (Slice of Life, Drama) -> Status CURRENT (unscored -> reduced weight)
    # 3: mal_id=3, score=10.0 (Sci-Fi, Mecha) -> Status DROPPED (should be ignored)
    mock_anime_list = [
        {"mal_id": 1, "score": 9.0, "status": "COMPLETED", "title": "Action Hero"},
        {"mal_id": 2, "score": 0.0, "status": "CURRENT", "title": "Chill Vibes"},
        {"mal_id": 3, "score": 10.0, "status": "DROPPED", "title": "Space Opera"},
    ]

    with patch("services.taste_profile.get_anilist_user", return_value=user_record), \
         patch("services.taste_profile.fetch_user_anime_list", return_value=mock_anime_list), \
         patch("services.taste_profile.get_likes", return_value=[]):
        
        profile_data = compute_taste_profile("user_test_42")
        anilist_breakdown = profile_data["breakdown"]["anilist"]
        
        # mal_id=1: score=9.0 -> weight = (9.0/10.0) * 2.0 = 1.8
        assert "action" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["action"]) == 1.8
        assert "shonen" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["shonen"]) == 1.8
        
        # mal_id=2: score=0.0 -> default weight = 0.5 * 2.0 = 1.0
        assert "slice of life" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["slice of life"]) == 1.0
        assert "drama" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["drama"]) == 1.0
        
        # mal_id=3 (DROPPED): should be ignored
        assert "sci-fi" not in anilist_breakdown
        assert "mecha" not in anilist_breakdown


def test_null_idmal_entry_skipped():
    """An entry with null idMal is skipped without affecting the rest of the signal."""
    user_record = {
        "user_id": "user_test_42",
        "anilist_id": 12345,
        "access_token": "token_xyz"
    }
    
    # Entry with null mal_id should be silently skipped,
    # and the rated entry (mal_id=1) should still score correctly.
    mock_anime_list = [
        {"mal_id": 1, "score": 8.0, "status": "COMPLETED", "title": "Action Hero"},
        # This entry has no mal_id — simulates null idMal from AniList
        {"mal_id": None, "score": 10.0, "status": "COMPLETED", "title": "AniList-only Entry"},
    ]
    
    # Filter out None mal_ids the same way fetch_user_anime_list does
    filtered_list = [e for e in mock_anime_list if e.get("mal_id") is not None]
    
    with patch("services.taste_profile.get_anilist_user", return_value=user_record), \
         patch("services.taste_profile.fetch_user_anime_list", return_value=filtered_list), \
         patch("services.taste_profile.get_likes", return_value=[]):
        
        profile_data = compute_taste_profile("user_test_42")
        anilist_breakdown = profile_data["breakdown"]["anilist"]
        
        # mal_id=1: score=8.0 -> weight = (8.0/10.0) * 2.0 = 1.6
        assert "action" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["action"]) == 1.6
        assert "shonen" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["shonen"]) == 1.6


def test_large_unrated_backlog_reduced_weight():
    """A large unrated backlog (50 entries, score=0) contributes reduced weight.
    Rated entries still dominate with score-proportional weights.
    """
    user_record = {
        "user_id": "user_test_42",
        "anilist_id": 12345,
        "access_token": "token_xyz"
    }

    # 50 unrated entries watching mal_id=2 (Slice of Life, Drama)
    unrated_entries = [
        {"mal_id": 2, "score": 0.0, "status": "CURRENT", "title": "Chill Vibes"}
        for _ in range(50)
    ]
    # 2 rated entries
    rated_entries = [
        {"mal_id": 1, "score": 9.0, "status": "COMPLETED", "title": "Action Hero"},
        {"mal_id": 4, "score": 7.0, "status": "COMPLETED", "title": "Romance Tale"},
    ]
    
    mock_anime_list = unrated_entries + rated_entries

    with patch("services.taste_profile.get_anilist_user", return_value=user_record), \
         patch("services.taste_profile.fetch_user_anime_list", return_value=mock_anime_list), \
         patch("services.taste_profile.get_likes", return_value=[]):
        
        profile_data = compute_taste_profile("user_test_42")
        anilist_breakdown = profile_data["breakdown"]["anilist"]
        
        # Unrated entries: 50 × (0.5 * 2.0) = 50.0 per genre
        assert "slice of life" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["slice of life"]) == 50.0
        assert "drama" in anilist_breakdown
        assert pytest.approx(anilist_breakdown["drama"]) == 50.0
        
        # Rated entries should score correctly
        # mal_id=1: score=9.0 -> weight = 1.8
        assert pytest.approx(anilist_breakdown["action"]) == 1.8
        assert pytest.approx(anilist_breakdown["shonen"]) == 1.8
        # mal_id=4: score=7.0 -> weight = (7.0/10.0) * 2.0 = 1.4
        assert pytest.approx(anilist_breakdown["romance"]) == 1.4
        assert pytest.approx(anilist_breakdown["comedy"]) == 1.4


def test_taste_profile_includes_anilist_watched_connected_with_entries(auth_override):
    """/taste-profile response includes anilist_watched for a connected account with rated entries."""
    client = TestClient(app)
    user_record = {
        "user_id": auth_override,
        "anilist_id": 12345,
        "access_token": "token_xyz"
    }
    mock_anime_list = [
        {"mal_id": 1, "score": 9.0, "status": "COMPLETED", "title": "Action Hero"},
        {"mal_id": 2, "score": 0.0, "status": "CURRENT", "title": "Chill Vibes"},
    ]

    with patch("routers.taste.get_anilist_user", return_value=user_record), \
         patch("services.taste_profile.get_anilist_user", return_value=user_record), \
         patch("services.taste_profile.fetch_user_anime_list", return_value=mock_anime_list), \
         patch("services.taste_profile.get_likes", return_value=[]):
        response = client.get("/taste-profile")
        assert response.status_code == 200
        data = response.json()

        assert data["anilist_connected"] is True
        assert "anilist_watched" in data
        # Both COMPLETED and CURRENT entries appear in anilist_watched
        # (anilist_watched is the raw list, not the signal — signal filters by score)
        watched_ids = [e["mal_id"] for e in data["anilist_watched"]]
        assert 1 in watched_ids
        assert 2 in watched_ids


def test_taste_profile_includes_anilist_watched_connected_empty_list(auth_override):
    """/taste-profile response includes anilist_watched (empty) for a connected account with no entries."""
    client = TestClient(app)
    user_record = {
        "user_id": auth_override,
        "anilist_id": 12345,
        "access_token": "token_xyz"
    }

    with patch("routers.taste.get_anilist_user", return_value=user_record), \
         patch("services.taste_profile.get_anilist_user", return_value=user_record), \
         patch("services.taste_profile.fetch_user_anime_list", return_value=[]), \
         patch("services.taste_profile.get_likes", return_value=[]):
        response = client.get("/taste-profile")
        assert response.status_code == 200
        data = response.json()

        assert data["anilist_connected"] is True
        assert "anilist_watched" in data
        assert data["anilist_watched"] == []
        # Signal should be empty too
        assert data["breakdown"]["anilist"] == {}


def test_connections_status_connected_with_entries(auth_override):
    """/connections/status reports anilist: true for a connected account (even if list is empty)."""
    client = TestClient(app)
    anilist_record = {
        "user_id": auth_override,
        "anilist_id": 12345,
        "access_token": "token_xyz"
    }

    with patch("routers.connections.get_user", return_value=None), \
         patch("routers.connections.get_anilist_user", return_value=anilist_record):
        response = client.get("/connections/status")
        assert response.status_code == 200
        data = response.json()
        assert data["anilist"] is True
        assert data["spotify"] is False


def test_connections_status_connected_empty_list(auth_override):
    """/connections/status reports anilist: true for connected-but-empty-list account."""
    client = TestClient(app)
    anilist_record = {
        "user_id": auth_override,
        "anilist_id": 12345,
        "access_token": "token_xyz"
    }

    with patch("routers.connections.get_user", return_value=None), \
         patch("routers.connections.get_anilist_user", return_value=anilist_record):
        response = client.get("/connections/status")
        assert response.status_code == 200
        data = response.json()
        # Connected is about account linkage, not list content
        assert data["anilist"] is True


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
            {"mal_id": 2, "score": 10.0, "status": "COMPLETED", "title": "Chill Vibes"},
        ]
        with patch("services.taste_profile.get_anilist_user", return_value=user_record), \
             patch("services.taste_profile.fetch_user_anime_list", return_value=mock_anime_list), \
             patch("services.taste_profile.get_likes", return_value=[]), \
             patch("routers.taste.get_anilist_user", return_value=user_record):
            resp_after = client.get("/anime/5/recommend?personalize=true")
            assert resp_after.status_code == 200
            data_after = resp_after.json()

            # The recommendations before vs after should have different ordering/scores
            ids_before = [x["mal_id"] for x in data_before["recommendations"]]
            ids_after = [x["mal_id"] for x in data_after["recommendations"]]
            
            # Verify they did not return empty
            assert len(ids_before) > 0
            assert len(ids_after) > 0
            
            # Check boost map directly to be sure it boosts "slice of life" and "drama"
            boosts = get_anime_boost_map("user_test_42")
            assert boosts.get("slice of life") == 2.0
            assert boosts.get("drama") == 2.0
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)
