import pytest
from fastapi.testclient import TestClient
from main import app
from services.auth import create_state_token, verify_state_token, create_session_cookie
from database import upsert_anilist_user, get_anilist_user, upsert_google_user, get_db
from fastapi import HTTPException

client = TestClient(app)

def test_state_token_helpers():
    # Test valid state token flow
    user_id = "test_user_123"
    token = create_state_token(user_id)
    assert token is not None
    assert isinstance(token, str)

    verified_user_id = verify_state_token(token)
    assert verified_user_id == user_id

    # Test invalid token raises HTTPException
    with pytest.raises(HTTPException) as exc_info:
        verify_state_token("invalid_token_xyz")
    assert exc_info.value.status_code == 401

def test_database_helpers():
    # Insert a user to satisfy foreign key constraints if they are enforced
    user_id = "9999"
    upsert_google_user(google_sub="google_sub_9999", email="test@test.com", name="Test User", picture_url="")
    
    # Test upsert and get
    upsert_anilist_user(user_id=user_id, anilist_id=12345, anilist_username="anilist_dev", access_token="token_abc")
    
    anilist_user = get_anilist_user(user_id)
    assert anilist_user is not None
    assert anilist_user["user_id"] == user_id
    assert anilist_user["anilist_id"] == 12345
    assert anilist_user["anilist_username"] == "anilist_dev"
    assert anilist_user["access_token"] == "token_abc"

def test_anilist_login_endpoint():
    # 1. Unauthenticated request -> should return 401
    response = client.get("/anilist/login")
    assert response.status_code == 401

    # 2. Authenticated request -> should redirect to AniList authorize URL
    session_cookie = create_session_cookie("9999")
    response = client.get("/anilist/login", cookies={"session": session_cookie}, follow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    redirect_url = response.headers.get("location", "")
    assert "anilist.co/api/v2/oauth/authorize" in redirect_url
    assert "state=" in redirect_url

def test_anilist_status_endpoint():
    # 1. Unauthenticated request -> should return 401
    response = client.get("/anilist/status")
    assert response.status_code == 401

    # 2. Authenticated but not connected request -> connected: false
    # Let's use a new user
    session_cookie = create_session_cookie("8888")
    response = client.get("/anilist/status", cookies={"session": session_cookie})
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False
    assert data["anilist_username"] is None

    # 3. Connected request -> connected: true
    session_cookie_connected = create_session_cookie("9999")
    response = client.get("/anilist/status", cookies={"session": session_cookie_connected})
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["anilist_username"] == "anilist_dev"
