import os
import time
import requests
import base64
import torch
from collections import defaultdict
from typing import List, Dict, Any, Set
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from database import get_user, upsert_user, delete_user
from models.spotify_dnn import SpotifySimilarityDNN

load_dotenv()

router = APIRouter(prefix="/spotify", tags=["spotify"])

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

TEST_USER_ID = "test_user_123"

# Load PyTorch model at cold start
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
spotify_model = SpotifySimilarityDNN(input_dim=10, hidden_dim=32).to(device)

model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'models', 'spotify_model.pth')
if os.path.exists(model_path):
    spotify_model.load_state_dict(torch.load(model_path, map_location=device))
spotify_model.eval()

def get_auth_header():
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {b64_auth_str}"}

def refresh_spotify_token(user: Dict[str, Any]):
    url = "https://accounts.spotify.com/api/token"
    headers = get_auth_header()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": user.get("refresh_token")
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to refresh token")
    
    token_info = response.json()
    new_access_token = token_info["access_token"]
    new_refresh_token = token_info.get("refresh_token", user.get("refresh_token"))
    new_expires_at = int(time.time()) + token_info["expires_in"]
    
    upsert_user(TEST_USER_ID, new_access_token, new_refresh_token, new_expires_at)
    return new_access_token

def get_valid_access_token(user_id: str):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not logged in with Spotify. Please visit /spotify/login")
    
    if int(time.time()) > int(user.get("expires_at", 0)):
        return refresh_spotify_token(user)
    return user.get("access_token")

@router.get("/login")
def login_to_spotify():
    scope = "user-top-read user-library-read"
    url = (
        f"https://accounts.spotify.com/authorize?response_type=code"
        f"&client_id={SPOTIFY_CLIENT_ID}"
        f"&scope={scope}"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
    )
    return RedirectResponse(url)

@router.get("/callback")
def spotify_callback(code: str):
    url = "https://accounts.spotify.com/api/token"
    headers = get_auth_header()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get token")
    
    token_info = response.json()
    access_token = token_info["access_token"]
    refresh_token = token_info.get("refresh_token")
    expires_at = int(time.time()) + token_info["expires_in"]
    
    upsert_user(TEST_USER_ID, access_token, refresh_token, expires_at)
    return {"message": "Successfully logged in to Spotify!"}

@router.get("/top-tracks")
def get_top_tracks():
    token = get_valid_access_token(TEST_USER_ID)
    url = "https://api.spotify.com/v1/me/top/tracks?limit=10"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch top tracks")
    
    data = response.json()
    cleaned_tracks = [
        {
            "id": item["id"],
            "name": item["name"],
            "artists": [artist["name"] for artist in item["artists"]],
            "album": item["album"]["name"],
            "popularity": item["popularity"]
        }
        for item in data.get("items", [])
    ]
    return {"top_tracks": cleaned_tracks}

def fetch_audio_features(track_ids: List[str], token: str) -> Dict[str, Dict[str, float]]:
    if not track_ids:
        return {}
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/audio-features?ids={','.join(track_ids)}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch audio features: {response.status_code}")
        return {}
    
    features = {}
    for item in response.json().get("audio_features", []):
        if item:
            features[item["id"]] = {
                "danceability": item.get("danceability", 0.0),
                "energy": item.get("energy", 0.0),
                "tempo": item.get("tempo", 0.0),
                "valence": item.get("valence", 0.0),
                "acousticness": item.get("acousticness", 0.0)
            }
    return features

@router.get("/recommend/{track_id}")
def recommend_similar_tracks(track_id: str):
    """
    Passes audio features into our PyTorch DNN to get similarity scores.
    """
    token = get_valid_access_token(TEST_USER_ID)
    
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.spotify.com/v1/me/top/tracks?limit=50"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch top tracks")
    
    top_tracks = response.json().get("items", [])
    if not top_tracks:
        return {"recommendations": []}
        
    candidate_ids = [track["id"] for track in top_tracks if track["id"] != track_id]
    ids_to_fetch = [track_id] + candidate_ids
    ids_to_fetch = ids_to_fetch[:100]
    
    audio_features_map = fetch_audio_features(ids_to_fetch, token)
    
    if track_id not in audio_features_map:
        raise HTTPException(status_code=404, detail="Seed track audio features not found")
        
    seed_features = audio_features_map[track_id]
    
    def normalize_features(features: Dict[str, float]) -> List[float]:
        return [
            features["danceability"],
            features["energy"],
            min(features["tempo"] / 200.0, 1.0),
            features["valence"],
            features["acousticness"]
        ]
        
    seed_vector = torch.tensor(normalize_features(seed_features), dtype=torch.float32).to(device)
    
    recommendations = []
    with torch.no_grad():
        for track in top_tracks:
            tid = track["id"]
            if tid == track_id or tid not in audio_features_map:
                continue
                
            candidate_vector = torch.tensor(normalize_features(audio_features_map[tid]), dtype=torch.float32).to(device)
            # PyTorch inference
            similarity = spotify_model(seed_vector, candidate_vector).item()
            
            recommendations.append({
                "id": tid,
                "name": track["name"],
                "artists": [a["name"] for a in track.get("artists", [])],
                "similarity_score": round(similarity, 4)
            })
        
    recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
    return {"recommendations": recommendations[:5]}
