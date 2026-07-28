import os
import time
import requests
import base64
import torch
from collections import defaultdict
from typing import List, Dict, Any, Set, Optional
from fastapi import APIRouter, HTTPException, Query, Response, Depends
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from services.auth import create_session_cookie, get_current_user_id
from database import get_user, upsert_user, delete_user
from models.spotify_dnn import SpotifySimilarityDNN

load_dotenv()

router = APIRouter(prefix="/spotify", tags=["spotify"])

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# ---------------------------------------------------------------------------
# Broad genre categories used for normalisation.
# Order matters for substring matching — longer/more-specific entries first
# to avoid "hip" matching before "hip hop".
# ---------------------------------------------------------------------------
BROAD_CATEGORIES: List[str] = [
    "hip hop", "r&b", "rock", "metal", "pop", "rap",
    "jazz", "classical", "electronic", "indie", "folk", "country",
]


# ===========================================================================
# GENRE-PROFILE CONTENT-SCORING FUNCTIONS
# These power the /spotify/recommendations endpoint (the non-deprecated path).
# ===========================================================================

def normalize_genres(raw: List[str]) -> List[str]:
    """
    Map raw Spotify genre strings to broad categories by substring matching.

    For every raw genre string:
      - Check whether any broad category appears as a substring of the raw string.
      - If yes, include the matched broad category in the result (in addition to
        keeping the original raw string).
      - If no broad category matches, keep the raw string as-is.

    Returns a deduplicated list preserving insertion order.

    Example
    -------
    >>> normalize_genres(["shiver pop", "indie rock", "ambient"])
    ["shiver pop", "pop", "indie rock", "indie", "rock", "ambient"]
    """
    seen: set = set()
    result: List[str] = []

    for genre in raw:
        if genre not in seen:
            seen.add(genre)
            result.append(genre)

        matched_any = False
        for category in BROAD_CATEGORIES:
            if category in genre.lower():
                matched_any = True
                if category not in seen:
                    seen.add(category)
                    result.append(category)

    return result


def compute_genre_profile(artists: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Build a weighted genre profile from a ranked list of artists.

    Artist at index ``i`` out of ``n`` total artists receives weight
    ``(n - i) / n``.  Each genre listed on that artist has that weight
    added to the accumulator.  Genres are used as-is (call
    ``normalize_genres`` on them beforehand if you want broad-category
    bucketing).

    Returns an empty dict when ``artists`` is empty.

    Example
    -------
    With 3 artists [pop], [rock], [pop, indie]:
      index 0: weight = 3/3 = 1.00 → pop += 1.00
      index 1: weight = 2/3 ≈ 0.67 → rock += 0.67
      index 2: weight = 1/3 ≈ 0.33 → pop += 0.33, indie += 0.33
    Result: {pop: 1.33, rock: 0.67, indie: 0.33}
    """
    if not artists:
        return {}

    n = len(artists)
    profile: Dict[str, float] = defaultdict(float)

    for i, artist in enumerate(artists):
        weight = (n - i) / n
        for genre in artist.get("genres", []):
            profile[genre] += weight

    return dict(profile)


def score_candidate_tracks(
    candidates: List[Dict[str, Any]],
    user_profile: Dict[str, float],
    track_genres_map: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    """
    Score each candidate track against a user genre profile.

    For each candidate the score is the sum of profile weights for every
    genre the track belongs to (genres looked up from ``track_genres_map``).
    Tracks with a score of 0 (no genre overlap) are excluded.

    Returns candidates sorted descending by score, each with a ``"score"``
    key added.

    Parameters
    ----------
    candidates:
        List of track dicts that must contain at least ``"id"``.
    user_profile:
        Mapping of genre → accumulated weight from ``compute_genre_profile``.
    track_genres_map:
        Mapping of track_id → list of genre strings.
    """
    scored: List[Dict[str, Any]] = []

    for track in candidates:
        track_id = track["id"]
        genres = track_genres_map.get(track_id, [])
        score = sum(user_profile.get(g, 0.0) for g in genres)
        if score > 0:
            result = dict(track)
            result["score"] = round(score, 4)
            result["matched_genres"] = [g for g in genres if g in user_profile]
            scored.append(result)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def get_artist_genres(artist_id: str, token: str) -> List[str]:
    """
    Fetch genres for a single artist from the Spotify API.

    GET https://api.spotify.com/v1/artists/{artist_id}

    Returns the ``genres`` list from the response, or ``[]`` on any error.
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get("genres", [])
    except Exception as e:
        print(f"[spotify] get_artist_genres({artist_id}): {e}")
    return []


def search_candidates(
    top_genres: List[str],
    exclude_ids: Set[str],
    token: str,
    limit_per_genre: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search Spotify for candidate tracks across a list of genres.

    For each genre string in ``top_genres``, issues:
        GET /v1/search?q=genre:<genre>&type=track&limit=<limit_per_genre>

    Deduplicates by track id and excludes any id in ``exclude_ids``.

    Returns a list of track dicts with keys: id, name, artists (list of
    artist name strings), album.
    """
    headers = {"Authorization": f"Bearer {token}"}
    seen_ids: Set[str] = set(exclude_ids)
    candidates: List[Dict[str, Any]] = []

    for genre in top_genres:
        url = "https://api.spotify.com/v1/search"
        params = {
            "q": f"genre:{genre}",
            "type": "track",
            "limit": limit_per_genre,
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code != 200:
                print(f"[spotify] search_candidates: {response.status_code} for genre={genre}")
                continue
            items = response.json().get("tracks", {}).get("items", [])
            for item in items:
                tid = item.get("id")
                if not tid or tid in seen_ids:
                    continue
                seen_ids.add(tid)
                candidates.append({
                    "id": tid,
                    "name": item.get("name", ""),
                    "artists": [a["name"] for a in item.get("artists", [])],
                    "album": item.get("album", {}).get("name", ""),
                })
        except Exception as e:
            print(f"[spotify] search_candidates({genre}): {e}")

    return candidates


def score_candidates(
    candidates: List[Dict[str, Any]],
    user_profile: Dict[str, float],
    token: str,
) -> List[Dict[str, Any]]:
    """
    Fetch genres for each candidate from Spotify, then delegate to
    ``score_candidate_tracks``.

    This is the "online" variant used by the /recommendations endpoint and
    the leave-one-out eval script (it fetches genres via the API so the
    caller doesn't need to build track_genres_map manually).
    """
    if not candidates:
        return []

    headers = {"Authorization": f"Bearer {token}"}
    track_genres_map: Dict[str, List[str]] = {}

    # Fetch artist genres in bulk for the artists on each candidate track.
    # Spotify has no bulk track→genre endpoint; we proxy through artists.
    artist_genre_cache: Dict[str, List[str]] = {}

    for track in candidates:
        # `artists` here is a list of name strings (from search_candidates).
        # We need to re-fetch artist objects to get their ids and genres.
        # For now we search by name (best-effort).
        # The /recommendations endpoint passes full artist dicts via a
        # separate artist_ids_map; this function accepts only what
        # search_candidates returns, so we do a quick artist search.
        all_genres: List[str] = []
        # We piggy-back on the track's artist names to look up genres;
        # track dicts may carry "_artist_ids" if injected by the endpoint.
        artist_ids = track.get("_artist_ids", [])
        for aid in artist_ids:
            if aid not in artist_genre_cache:
                artist_genre_cache[aid] = get_artist_genres(aid, token)
            all_genres.extend(artist_genre_cache[aid])

        track_genres_map[track["id"]] = list(set(all_genres))

    return score_candidate_tracks(candidates, user_profile, track_genres_map)


# ===========================================================================
# AUTH HELPERS
# ===========================================================================

def get_auth_header() -> Dict[str, str]:
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {b64_auth_str}"}


def refresh_spotify_token(user: Dict[str, Any]) -> str:
    url = "https://accounts.spotify.com/api/token"
    headers = get_auth_header()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": user.get("refresh_token"),
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to refresh token")

    token_info = response.json()
    new_access_token = token_info["access_token"]
    new_refresh_token = token_info.get("refresh_token", user.get("refresh_token"))
    new_expires_at = int(time.time()) + token_info["expires_in"]

    upsert_user(user["user_id"], new_access_token, new_refresh_token, new_expires_at)
    return new_access_token


def get_valid_access_token(user_id: str) -> str:
    """Return a valid Spotify access token for *user_id*, refreshing if needed."""
    user = get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not logged in with Spotify. Please visit /spotify/login",
        )
    if int(time.time()) > int(user.get("expires_at", 0)):
        return refresh_spotify_token(user)
    return user.get("access_token")


# ===========================================================================
# ROUTES — OAuth
# ===========================================================================

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
def spotify_callback(response: Response, code: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail="Spotify login was cancelled or denied")
    if not code and not error:
        raise HTTPException(status_code=400, detail="Login must start at /spotify/login")

    url = "https://accounts.spotify.com/api/token"
    headers = get_auth_header()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
    }
    token_response = requests.post(url, headers=headers, data=data)
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get token")

    token_info = token_response.json()
    access_token = token_info["access_token"]
    refresh_token = token_info.get("refresh_token")
    expires_at = int(time.time()) + token_info["expires_in"]

    user_response = requests.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user profile")
    
    spotify_user_id = user_response.json()["id"]

    upsert_user(spotify_user_id, access_token, refresh_token, expires_at)
    
    cookie_value = create_session_cookie(spotify_user_id)
    response.set_cookie(
        key="session",
        value=cookie_value,
        httponly=True,
        samesite="lax"
    )

    response.status_code = 302
    response.headers["Location"] = "http://localhost:5173/"
    return response


# ===========================================================================
# ROUTES — Data fetching
# ===========================================================================

@router.get("/top-tracks")
def get_top_tracks(user_id: str = Depends(get_current_user_id)):
    token = get_valid_access_token(user_id)
    url = "https://api.spotify.com/v1/me/top/tracks?limit=10"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch top tracks"
        )

    data = response.json()
    cleaned_tracks = [
        {
            "id": item["id"],
            "name": item["name"],
            "artists": [artist["name"] for artist in item["artists"]],
            "album": item["album"]["name"],
            "popularity": item["popularity"],
        }
        for item in data.get("items", [])
    ]
    return {"top_tracks": cleaned_tracks}


# ===========================================================================
# ROUTES — Genre-profile recommendations (primary / non-deprecated path)
# ===========================================================================

@router.get("/recommendations")
def get_recommendations(limit: int = Query(default=10, ge=1, le=50), user_id: str = Depends(get_current_user_id)):
    """
    Content-based genre-profile recommendations.

    1. Fetch the user's top 50 artists (ranked).
    2. Normalise and weight their genres into a profile.
    3. Search Spotify for candidate tracks in the top profile genres.
    4. Score candidates by genre overlap with the profile.
    5. Exclude tracks already in the user's top-tracks / saved library.
    6. Return the top ``limit`` results.

    Note: This path does NOT use the deprecated /audio-features API.
    """
    token = get_valid_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # --- 1. Fetch top artists ---
    artists_resp = requests.get(
        "https://api.spotify.com/v1/me/top/artists?limit=50", headers=headers
    )
    if artists_resp.status_code != 200:
        raise HTTPException(
            status_code=artists_resp.status_code,
            detail="Failed to fetch top artists",
        )
    artists = artists_resp.json().get("items", [])

    if not artists:
        return {"recommendations": [], "genre_profile": {}}

    # --- 2. Normalise genres and build profile ---
    for artist in artists:
        artist["genres"] = normalize_genres(artist.get("genres", []))

    user_profile = compute_genre_profile(artists)
    sorted_genres = sorted(user_profile, key=user_profile.get, reverse=True)
    top_genres = sorted_genres[:5]

    # --- 3. Build exclusion set from user's own top tracks ---
    top_tracks_resp = requests.get(
        "https://api.spotify.com/v1/me/top/tracks?limit=50", headers=headers
    )
    exclude_ids: Set[str] = set()
    if top_tracks_resp.status_code == 200:
        exclude_ids = {t["id"] for t in top_tracks_resp.json().get("items", [])}

    # --- 4. Search candidates ---
    raw_candidates = search_candidates(top_genres, exclude_ids, token)

    # Inject artist ids so score_candidates can fetch genres
    # We re-search to get artist ids for each candidate track
    artist_genre_cache: Dict[str, List[str]] = {}
    track_genres_map: Dict[str, List[str]] = {}

    for track in raw_candidates:
        # Re-fetch track detail to get artist ids (search result already has them)
        # search_candidates strips to name strings; inject _artist_ids here
        pass  # handled below via a separate search call

    # Simpler: re-fetch track details for all candidate ids in one batch
    candidate_ids = [t["id"] for t in raw_candidates]
    CHUNK = 50
    track_details: Dict[str, Any] = {}
    for i in range(0, len(candidate_ids), CHUNK):
        chunk = candidate_ids[i : i + CHUNK]
        resp = requests.get(
            f"https://api.spotify.com/v1/tracks?ids={','.join(chunk)}",
            headers=headers,
        )
        if resp.status_code == 200:
            for t in resp.json().get("tracks", []) or []:
                if t:
                    track_details[t["id"]] = t

    # Fetch genres per artist (cached)
    for track in raw_candidates:
        tid = track["id"]
        detail = track_details.get(tid, {})
        all_genres: List[str] = []
        for artist_obj in detail.get("artists", []):
            aid = artist_obj.get("id")
            if aid:
                if aid not in artist_genre_cache:
                    artist_genre_cache[aid] = normalize_genres(
                        get_artist_genres(aid, token)
                    )
                all_genres.extend(artist_genre_cache[aid])
        track_genres_map[tid] = list(set(all_genres))

    # --- 5. Score ---
    scored = score_candidate_tracks(raw_candidates, user_profile, track_genres_map)

    return {
        "recommendations": scored[:limit],
        "genre_profile": {g: round(user_profile[g], 3) for g in sorted_genres[:10]},
    }


# ===========================================================================
# [DEPRECATED] DNN / audio-features path
# ===========================================================================
# The Spotify /audio-features endpoint was deprecated for new Developer apps
# in November 2024 (see README note).  The code below is kept for reference
# and for apps that were granted access before the deprecation cut-off, but
# it is NOT the primary recommendation path.  Use GET /spotify/recommendations
# above instead.
# ===========================================================================

# Load PyTorch model at cold start (only used by the deprecated endpoint)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
spotify_model = SpotifySimilarityDNN(input_dim=10, hidden_dim=32).to(device)

_model_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "models",
    "spotify_model.pth",
)
if os.path.exists(_model_path):
    spotify_model.load_state_dict(torch.load(_model_path, map_location=device))
spotify_model.eval()


def fetch_audio_features(track_ids: List[str], token: str) -> Dict[str, Dict[str, float]]:
    """[DEPRECATED] Fetch audio features via the /audio-features endpoint."""
    if not track_ids:
        return {}

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/audio-features?ids={','.join(track_ids)}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"[DEPRECATED] Failed to fetch audio features: {response.status_code}")
        return {}

    features = {}
    for item in response.json().get("audio_features", []):
        if item:
            features[item["id"]] = {
                "danceability": item.get("danceability", 0.0),
                "energy": item.get("energy", 0.0),
                "tempo": item.get("tempo", 0.0),
                "valence": item.get("valence", 0.0),
                "acousticness": item.get("acousticness", 0.0),
            }
    return features


@router.get(
    "/recommend/{track_id}",
    deprecated=True,
    summary="[DEPRECATED] DNN similarity via audio-features",
    description=(
        "Uses the Spotify /audio-features endpoint which was deprecated for new apps "
        "in November 2024.  For new integrations use GET /spotify/recommendations instead."
    ),
)
def recommend_similar_tracks(track_id: str, user_id: str = Depends(get_current_user_id)):
    """
    [DEPRECATED] Passes audio features into the PyTorch DNN to get similarity scores.
    Requires /audio-features API access (not available for new Spotify Developer apps
    created after November 2024).  Use /spotify/recommendations instead.
    """
    token = get_valid_access_token(user_id)

    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.spotify.com/v1/me/top/tracks?limit=50"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch top tracks"
        )

    top_tracks = response.json().get("items", [])
    if not top_tracks:
        return {"recommendations": []}

    candidate_ids = [track["id"] for track in top_tracks if track["id"] != track_id]
    ids_to_fetch = [track_id] + candidate_ids
    ids_to_fetch = ids_to_fetch[:100]

    audio_features_map = fetch_audio_features(ids_to_fetch, token)

    if track_id not in audio_features_map:
        raise HTTPException(
            status_code=404, detail="Seed track audio features not found"
        )

    seed_features = audio_features_map[track_id]

    def _normalize(features: Dict[str, float]) -> List[float]:
        return [
            features["danceability"],
            features["energy"],
            min(features["tempo"] / 200.0, 1.0),
            features["valence"],
            features["acousticness"],
        ]

    seed_vector = torch.tensor(_normalize(seed_features), dtype=torch.float32).to(device)

    recommendations = []
    with torch.no_grad():
        for track in top_tracks:
            tid = track["id"]
            if tid == track_id or tid not in audio_features_map:
                continue

            candidate_vector = torch.tensor(
                _normalize(audio_features_map[tid]), dtype=torch.float32
            ).to(device)
            similarity = spotify_model(seed_vector, candidate_vector).item()

            recommendations.append(
                {
                    "id": tid,
                    "name": track["name"],
                    "artists": [a["name"] for a in track.get("artists", [])],
                    "similarity_score": round(similarity, 4),
                }
            )

    recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
    return {"recommendations": recommendations[:5]}
