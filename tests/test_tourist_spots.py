"""
tests/test_tourist_spots.py — Unit and integration tests for tourist spots catalog,
feedback recording, crosswalk personalization, and recommendation endpoints.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, TouristSpot, UserSpotFeedback
from services.auth import get_current_user_id
from services.taste_profile import compute_taste_profile, TOURISM_CROSSWALK
from services.tourist_spots import get_spots, get_spot_by_id, record_feedback, get_recommendations

client = TestClient(app)


@pytest.fixture
def auth_override():
    app.dependency_overrides[get_current_user_id] = lambda: "test_user_tourist"
    yield "test_user_tourist"
    app.dependency_overrides.pop(get_current_user_id, None)


def test_tourism_crosswalk_mappings_exist():
    assert "rock" in TOURISM_CROSSWALK
    assert "ambient" in TOURISM_CROSSWALK
    assert "electronic" in TOURISM_CROSSWALK
    assert "pop" in TOURISM_CROSSWALK
    assert "classical" in TOURISM_CROSSWALK
    assert "action" in TOURISM_CROSSWALK


def test_list_tourist_spots_endpoint():
    resp = client.get("/tourist-spots")
    assert resp.status_code == 200
    spots = resp.json()
    assert len(spots) >= 60  # 65 total spots seeded
    categories = {s["category"] for s in spots}
    assert "adventure_outdoor" in categories
    assert "chill_scenic" in categories
    assert "offbeat_indie" in categories


def test_list_tourist_spots_filter():
    resp = client.get("/tourist-spots?category=chill_scenic&price_tier=free")
    assert resp.status_code == 200
    spots = resp.json()
    assert len(spots) > 0
    for s in spots:
        assert s["category"] == "chill_scenic"
        assert s["price_tier"] == "free"


def test_get_tourist_spot_by_id():
    resp = client.get("/tourist-spots/writers-cafe")
    assert resp.status_code == 200
    spot = resp.json()
    assert spot["place_id"] == "writers-cafe"
    assert spot["category"] == "offbeat_indie"
    assert spot["name"] == "Writer's Cafe"


def test_get_tourist_spot_404():
    resp = client.get("/tourist-spots/nonexistent-spot-id")
    assert resp.status_code == 404


def test_spot_feedback_requires_auth():
    resp = client.post("/tourist-spots/writers-cafe/feedback", json={"rating": 1})
    assert resp.status_code == 401


def test_spot_feedback_recording_and_upsert(auth_override):
    db = SessionLocal()
    try:
        db.query(UserSpotFeedback).filter(UserSpotFeedback.user_id == auth_override).delete()
        db.commit()
    finally:
        db.close()

    # 1. Like
    resp = client.post("/tourist-spots/writers-cafe/feedback", json={"rating": 1, "tag": "quiet"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert data["rating"] == 1
    assert data["tag"] == "quiet"

    # 2. Upsert with dislike
    resp2 = client.post("/tourist-spots/writers-cafe/feedback", json={"rating": -1, "tag": "noisy"})
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["rating"] == -1
    assert data2["tag"] == "noisy"


def test_tourist_spot_recommendations_requires_auth():
    resp = client.get("/tourist-spots/recommendations")
    assert resp.status_code == 401


def test_tourist_spot_recommendations_ranked_by_taste(auth_override):
    user_id = auth_override
    # Mock Spotify energetic rock taste
    mock_spotify_artists = [
        {"id": "art1", "genres": ["rock", "metal"]},
    ]
    mock_resp = MagicMock(status_code=200, json=lambda: {"items": mock_spotify_artists})

    with patch("services.taste_profile.requests.get", return_value=mock_resp), \
         patch("services.taste_profile.get_likes", return_value=[]), \
         patch("routers.tourist_spots.get_user", return_value={"access_token": "valid_tok", "expires_at": 9999999999}):
        resp = client.get("/tourist-spots/recommendations?limit=10")

    assert resp.status_code == 200
    recs = resp.json()
    assert len(recs) == 10
    top_category = recs[0]["category"]
    # Rock/Metal leads to adventure_outdoor
    assert top_category == "adventure_outdoor"
