"""
services/anilist_client.py — AniList GraphQL API client.

Structure mirrors services/jikan_client.py:
- Shared POST helper with timeout/error handling
- Local-JSON fallback when S3_BUCKET_NAME is not set
- In-memory cache dict to avoid duplicate network calls within a Lambda instance
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from botocore.exceptions import ClientError

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

ANILIST_URL = "https://graphql.anilist.co"
JIKAN_URL = "https://api.jikan.moe/v4"

# ---------------------------------------------------------------------------
# In-Memory Cache (TTL)
# ---------------------------------------------------------------------------

_upcoming_cache: Optional[Dict[str, Any]] = None
_upcoming_fetched_at: float = 0.0
_UPCOMING_TTL = 14400  # 4 hours

_reviews_cache: Dict[int, Dict[str, Any]] = {}
_reviews_fetched_at: Dict[int, float] = {}
_REVIEWS_TTL = 3600  # 1 hour

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _anilist_post(query: str, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    POST a GraphQL query to the AniList public API.

    Returns the parsed JSON body on HTTP 200, or None on any error.
    No authentication is required — AniList's API is public.
    """
    try:
        response = requests.post(
            ANILIST_URL,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=8,
        )
        if response.status_code == 200:
            return response.json()
        print(f"[anilist] HTTP {response.status_code}: {response.text[:200]}")
    except Exception as exc:
        print(f"[anilist] Request error: {exc}")
    return None


def _current_season_and_year() -> tuple[str, int]:
    """
    Return the AniList season name and year for the current UTC date.
    Seasons: WINTER (Jan-Mar), SPRING (Apr-Jun), SUMMER (Jul-Sep), FALL (Oct-Dec).
    Returns next season if we are in the last month of the current one.
    """
    now = datetime.now(tz=timezone.utc)
    month = now.month
    year = now.year

    if month in (1, 2, 3):
        season = "SPRING"  # upcoming from WINTER's perspective
        if month == 3:
            season = "SPRING"
        else:
            season = "WINTER"
    elif month in (4, 5, 6):
        season = "SPRING"
    elif month in (7, 8, 9):
        season = "SUMMER"
    else:
        season = "FALL"

    # If we're in the last month of the season, return the *next* season
    # so "upcoming" actually means something not yet started.
    next_season_map = {
        "WINTER": ("SPRING", year),
        "SPRING": ("SUMMER", year),
        "SUMMER": ("FALL", year),
        "FALL": ("WINTER", year + 1),
    }
    if month in (3, 6, 9, 12):
        season, year = next_season_map[season]

    return season, year


# ---------------------------------------------------------------------------
# Upcoming anime
# ---------------------------------------------------------------------------

_UPCOMING_QUERY = """
query ($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int) {
  Page(page: $page, perPage: $perPage) {
    media(
      season: $season
      seasonYear: $seasonYear
      status: NOT_YET_RELEASED
      type: ANIME
      isAdult: false
    ) {
      id
      idMal
      title { romaji english }
      coverImage { medium }
      genres
      isAdult
      studios(isMain: true) { nodes { name } }
      description(asHtml: false)
      startDate { year month day }
    }
  }
}
"""


def _parse_upcoming_anilist(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalise AniList upcoming media list into our schema."""
    media_list = data.get("data", {}).get("Page", {}).get("media", []) or []
    results = []
    for item in media_list:
        if item.get("isAdult"):
            continue
            
        sd = item.get("startDate") or {}
        parts = [sd.get("year"), sd.get("month"), sd.get("day")]
        start_date = (
            f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
            if all(parts)
            else None
        )
        title_obj = item.get("title") or {}
        results.append(
            {
                "id": item.get("id"),
                "mal_id": item.get("idMal"),
                "title": title_obj.get("english") or title_obj.get("romaji"),
                "cover_image": (item.get("coverImage") or {}).get("medium"),
                "genres": item.get("genres") or [],
                "studios": [
                    n["name"]
                    for n in (item.get("studios") or {}).get("nodes", [])
                    if n.get("name")
                ],
                "description": item.get("description"),
                "start_date": start_date,
            }
        )
    return results


def _fetch_upcoming_jikan(limit: int) -> List[Dict[str, Any]]:
    """Jikan fallback for upcoming anime."""
    try:
        response = requests.get(
            f"{JIKAN_URL}/seasons/upcoming",
            params={"limit": min(limit, 25)},
            timeout=8,
        )
        if response.status_code == 200:
            items = response.json().get("data", [])
            results = []
            for item in items[:limit]:
                rating = item.get("rating") or ""
                if rating in ("Rx - Hentai", "R+ - Mild Nudity"):
                    continue
                    
                results.append(
                    {
                        "id": None,
                        "mal_id": item.get("mal_id"),
                        "title": item.get("title"),
                        "cover_image": (item.get("images") or {})
                        .get("jpg", {})
                        .get("image_url"),
                        "genres": [
                            g["name"] for g in (item.get("genres") or [])
                        ],
                        "studios": [
                            s["name"] for s in (item.get("studios") or [])
                        ],
                        "description": item.get("synopsis"),
                        "start_date": item.get("aired", {}).get("from"),
                    }
                )
            return results
        print(f"[jikan] upcoming HTTP {response.status_code}")
    except Exception as exc:
        print(f"[jikan] upcoming error: {exc}")
    return []


def fetch_upcoming_anime(per_page: int = 20) -> Dict[str, Any]:
    """
    Fetch upcoming anime from AniList, falling back to Jikan if AniList is
    unreachable.  Results are cached to ``data/raw/upcoming_anime.json`` when
    S3_BUCKET_NAME is not configured (local-dev mode).

    Returns a dict: {"source": "anilist"|"jikan"|"cache", "upcoming": [...]}
    """
    global _upcoming_cache, _upcoming_fetched_at
    now = time.time()

    if _upcoming_cache is not None and (now - _upcoming_fetched_at) <= _UPCOMING_TTL:
        return _upcoming_cache

    # Try AniList first
    season, year = _current_season_and_year()
    data = _anilist_post(
        _UPCOMING_QUERY,
        {"page": 1, "perPage": per_page, "season": season, "seasonYear": year},
    )
    if data:
        upcoming = _parse_upcoming_anilist(data)
        if upcoming:
            _cache_upcoming_local(upcoming)
            res = {"source": "anilist", "season": season, "year": year, "upcoming": upcoming}
            _upcoming_cache = res
            _upcoming_fetched_at = now
            return res

    print("[anilist] upcoming unavailable — trying Jikan fallback")
    upcoming = _fetch_upcoming_jikan(per_page)
    if upcoming:
        _cache_upcoming_local(upcoming)
        res = {"source": "jikan", "upcoming": upcoming}
        _upcoming_cache = res
        _upcoming_fetched_at = now
        return res

    if _upcoming_cache is not None:
        print("[anilist] Both sources failed. Serving stale upcoming cache.")
        return _upcoming_cache

    # Last resort: local cache
    cached = _load_upcoming_local()
    if cached:
        return {"source": "cache", "upcoming": cached}

    return {"source": "none", "upcoming": []}


def _cache_upcoming_local(upcoming: List[Dict[str, Any]]) -> None:
    if S3_BUCKET_NAME:
        return  # S3 path handled separately if needed
    os.makedirs("data/raw", exist_ok=True)
    try:
        with open("data/raw/upcoming_anime.json", "w") as f:
            json.dump(upcoming, f)
    except Exception as exc:
        print(f"[anilist] cache write error: {exc}")


def _load_upcoming_local() -> List[Dict[str, Any]]:
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "raw", "upcoming_anime.json",
    )
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return []


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

_REVIEWS_QUERY = """
query ($malId: Int, $page: Int, $perPage: Int) {
  Media(idMal: $malId, type: ANIME) {
    id
    title { romaji english }
    reviews(page: $page, perPage: $perPage, sort: RATING_DESC) {
      nodes {
        id
        score
        summary
        body
        user { name }
        createdAt
      }
    }
  }
}
"""


def _parse_reviews_anilist(mal_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise AniList reviews response."""
    media = data.get("data", {}).get("Media") or {}
    title_obj = media.get("title") or {}
    title = title_obj.get("english") or title_obj.get("romaji") or ""
    nodes = (media.get("reviews") or {}).get("nodes") or []

    reviews = []
    for node in nodes:
        # Truncate body to a short snippet (first 400 chars)
        body = node.get("body") or ""
        snippet = body[:400].rstrip() + ("…" if len(body) > 400 else "")
        created_ts = node.get("createdAt")
        created_at = (
            datetime.fromtimestamp(created_ts, tz=timezone.utc).isoformat()
            if created_ts
            else None
        )
        reviews.append(
            {
                "id": node.get("id"),
                "score": node.get("score"),
                "username": (node.get("user") or {}).get("name"),
                "summary": node.get("summary"),
                "snippet": snippet,
                "created_at": created_at,
            }
        )
    return {"source": "anilist", "mal_id": mal_id, "title": title, "reviews": reviews}


def _fetch_reviews_jikan(mal_id: int, per_page: int) -> Dict[str, Any]:
    """Jikan fallback for reviews."""
    try:
        response = requests.get(
            f"{JIKAN_URL}/anime/{mal_id}/reviews",
            params={"page": 1},
            timeout=8,
        )
        if response.status_code == 200:
            items = response.json().get("data", [])
            reviews = []
            for item in items[:per_page]:
                body = (item.get("review") or "")
                snippet = body[:400].rstrip() + ("…" if len(body) > 400 else "")
                reviews.append(
                    {
                        "id": item.get("mal_id"),
                        "score": (item.get("scores") or {}).get("overall"),
                        "username": (item.get("user") or {}).get("username"),
                        "summary": None,
                        "snippet": snippet,
                        "created_at": item.get("date"),
                    }
                )
            return {"source": "jikan", "mal_id": mal_id, "title": None, "reviews": reviews}
        print(f"[jikan] reviews HTTP {response.status_code}")
    except Exception as exc:
        print(f"[jikan] reviews error: {exc}")
    return {"source": "error", "mal_id": mal_id, "title": None, "reviews": []}


def fetch_reviews_by_mal_id(mal_id: int, per_page: int = 5) -> Dict[str, Any]:
    """
    Fetch reviews for an anime by its MAL ID, using AniList's ``idMal`` field.
    Falls back to Jikan's /anime/{mal_id}/reviews endpoint if AniList fails.
    """
    global _reviews_cache, _reviews_fetched_at
    now = time.time()

    if mal_id in _reviews_cache and (now - _reviews_fetched_at.get(mal_id, 0)) <= _REVIEWS_TTL:
        return _reviews_cache[mal_id]

    data = _anilist_post(
        _REVIEWS_QUERY,
        {"malId": mal_id, "page": 1, "perPage": per_page},
    )
    if data and data.get("data", {}).get("Media"):
        res = _parse_reviews_anilist(mal_id, data)
        _reviews_cache[mal_id] = res
        _reviews_fetched_at[mal_id] = now
        return res

    print(f"[anilist] reviews unavailable for mal_id={mal_id} — trying Jikan fallback")
    res = _fetch_reviews_jikan(mal_id, per_page)
    if res.get("source") != "error":
        _reviews_cache[mal_id] = res
        _reviews_fetched_at[mal_id] = now
        return res

    if mal_id in _reviews_cache:
        print(f"[anilist] Both sources failed. Serving stale reviews cache for mal_id={mal_id}.")
        return _reviews_cache[mal_id]

    return res

# ---------------------------------------------------------------------------
# Metadata (Cold-Start)
# ---------------------------------------------------------------------------

_METADATA_QUERY = """
query ($malId: Int) {
  Media(idMal: $malId, type: ANIME) {
    id
    idMal
    description(asHtml: false)
    genres
    tags {
      name
    }
  }
}
"""

def fetch_anime_metadata(mal_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch anime metadata for cold-start embedding generation.
    Retrieves description, genres, and tags from AniList.
    """
    data = _anilist_post(
        _METADATA_QUERY,
        {"malId": mal_id},
    )
    if data and data.get("data", {}).get("Media"):
        return data["data"]["Media"]
    
    print(f"[anilist] metadata unavailable for mal_id={mal_id}")
    return None


def fetch_user_anime_list(access_token: str, anilist_user_id: int) -> List[Dict[str, Any]]:
    """
    Fetch the authenticated user's complete anime list from AniList.
    """
    query = """
    query ($userId: Int) {
      MediaListCollection(userId: $userId, type: ANIME) {
        lists {
          entries {
            status
            score(format: POINT_10)
            media {
              idMal
              genres
              title {
                romaji
                english
              }
            }
          }
        }
      }
    }
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.post(
            ANILIST_URL,
            json={"query": query, "variables": {"userId": anilist_user_id}},
            headers=headers,
            timeout=8
        )
        if response.status_code != 200:
            print(f"[anilist] fetch_user_anime_list FAILED for user {anilist_user_id}: HTTP {response.status_code} — {response.text[:200]}")
            return []
            
        data = response.json()
        collection = data.get("data", {}).get("MediaListCollection") or {}
        lists = collection.get("lists") or []
        
        results = []
        for lst in lists:
            entries = lst.get("entries") or []
            for entry in entries:
                media = entry.get("media") or {}
                mal_id = media.get("idMal")
                if mal_id is None:
                    continue
                score = entry.get("score")
                try:
                    score_val = float(score) if score is not None else 0.0
                except (ValueError, TypeError):
                    score_val = 0.0
                
                title_obj = media.get("title") or {}
                title = title_obj.get("english") or title_obj.get("romaji") or "Unknown Title"
                
                results.append({
                    "mal_id": int(mal_id),
                    "score": score_val,
                    "status": entry.get("status"),
                    "title": title,
                    "genres": media.get("genres") or [],
                })
        return results
    except Exception as exc:
        print(f"[anilist] fetch_user_anime_list FAILED for user {anilist_user_id}: {exc}")
        return []

