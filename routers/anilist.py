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
    client_id = (os.getenv("ANILIST_CLIENT_ID") or "").strip()
    redirect_uri = (os.getenv("ANILIST_REDIRECT_URI") or "http://127.0.0.1:8000/anilist/callback").strip()
    state = create_state_token(user_id)
    print(f"[anilist_login] Initiating OAuth: client_id={client_id}, redirect_uri={redirect_uri}")
    url = (
        f"https://anilist.co/api/v2/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
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

    client_id = (os.getenv("ANILIST_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("ANILIST_CLIENT_SECRET") or "").strip()
    redirect_uri = (os.getenv("ANILIST_REDIRECT_URI") or "http://127.0.0.1:8000/anilist/callback").strip()

    print(f"[anilist_callback] Exchanging token: client_id={client_id} (len={len(client_id)}), client_secret_len={len(client_secret)}, redirect_uri={redirect_uri}")

    # exchange authorization code for access token
    token_url = "https://anilist.co/api/v2/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": int(client_id) if client_id.isdigit() else client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RecommendationApp/1.0",
        }
        response = requests.post(token_url, json=payload, headers=headers, timeout=10)
        print(f"[anilist_callback] AniList token response: status={response.status_code}, body={response.text}")
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"[anilist_callback] HTTP error from AniList: {response.text}")
        raise HTTPException(status_code=400, detail=f"Failed to exchange token with AniList: {response.text}")
    except Exception as e:
        print(f"[anilist_callback] Error during AniList token exchange: {e}")
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
