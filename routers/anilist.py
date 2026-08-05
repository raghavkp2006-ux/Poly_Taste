import os
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from services.auth import get_current_user_id, create_state_token, verify_state_token
from database import upsert_anilist_user, get_anilist_user

load_dotenv()

router = APIRouter(prefix="/anilist", tags=["anilist"])

ANILIST_CLIENT_ID = os.getenv("ANILIST_CLIENT_ID")
ANILIST_CLIENT_SECRET = os.getenv("ANILIST_CLIENT_SECRET")
ANILIST_REDIRECT_URI = os.getenv("ANILIST_REDIRECT_URI")

@router.get("/login")
def login(user_id: str = Depends(get_current_user_id)):
    state = create_state_token(user_id)
    url = (
        f"https://anilist.co/api/v2/oauth/authorize"
        f"?client_id={ANILIST_CLIENT_ID}"
        f"&redirect_uri={ANILIST_REDIRECT_URI}"
        f"&response_type=code"
        f"&state={state}"
    )
    return RedirectResponse(url)

@router.get("/callback")
def callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=f"AniList connection error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code or state")

    user_id = verify_state_token(state)

    # exchange authorization code for access token
    token_url = "https://anilist.co/api/v2/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": ANILIST_CLIENT_ID,
        "client_secret": ANILIST_CLIENT_SECRET,
        "redirect_uri": ANILIST_REDIRECT_URI,
        "code": code,
    }
    
    try:
        response = requests.post(token_url, json=payload, headers={"Content-Type": "application/json", "Accept": "application/json"})
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange token: {e}")

    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token returned from AniList")

    # Fetch Viewer profile from GraphQL
    graphql_url = "https://graphql.anilist.co"
    query = """
    query {
      Viewer {
        id
        name
      }
    }
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        res = requests.post(graphql_url, json={"query": query}, headers=headers)
        res.raise_for_status()
        viewer_data = res.json()
        viewer = viewer_data.get("data", {}).get("Viewer")
        if not viewer:
            raise ValueError("Viewer data not found in response")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch AniList viewer profile: {e}")

    anilist_id = viewer["id"]
    anilist_username = viewer["name"]

    upsert_anilist_user(
        user_id=user_id,
        anilist_id=anilist_id,
        anilist_username=anilist_username,
        access_token=access_token
    )

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(f"{FRONTEND_URL}/dashboard?anilist=connected")

@router.get("/status")
def status_endpoint(user_id: str = Depends(get_current_user_id)):
    anilist_user = get_anilist_user(user_id)
    if not anilist_user:
        return {"connected": False, "anilist_username": None}
    return {
        "connected": True,
        "anilist_username": anilist_user.get("anilist_username")
    }
