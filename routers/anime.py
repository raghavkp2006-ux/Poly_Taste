"""
routers/anime.py — Anime module router.

Endpoints
---------
Existing (unchanged logic):
  GET /anime/search               — substring search on catalog titles
  GET /anime/{mal_id}             — single anime detail from catalog
  GET /anime/{mal_id}/recommend   — TF-IDF / AutoEncoder similarity

New (added without touching existing logic):
  GET /anime/upcoming             — upcoming anime (AniList, Jikan fallback)
  GET /anime/{mal_id}/reviews     — reviews (AniList idMal lookup, Jikan fallback)
  GET /anime/{mal_id}/videos      — YouTube trailer/explainer search
  GET /anime/{mal_id}/news        — Anime News Network RSS filtered by title

Route-ordering note
-------------------
FastAPI resolves routes in registration order.  Static path segments (/search,
/upcoming) must be registered BEFORE parameterised segments (/{mal_id}) so
they are never mistakenly matched as integer params.
"""

import os
import time
from typing import Any, Dict, List, Optional

import feedparser
import requests
import pickle
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sklearn.feature_extraction.text import TfidfVectorizer

from database import add_like, remove_like, get_likes
from services.auth import get_current_user_id

from services.anilist_client import fetch_reviews_by_mal_id, fetch_upcoming_anime
from services.jikan_client import get_catalog_from_s3

from services.anime_recommender import (
    anime_data_map, 
    latent_matrix, latent_ids, get_or_compute_embedding
)

load_dotenv()

router = APIRouter(prefix="/anime", tags=["anime"])

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def _resolve_query(value: Any, fallback: int) -> int:
    """
    When route handlers are called directly in tests (bypassing FastAPI's ASGI
    machinery), Query() objects are passed as-is instead of being resolved to
    their declared default values.  This helper extracts the default from a
    FastAPI FieldInfo object, or returns the value itself if it is already an
    integer.
    """
    if isinstance(value, int):
        return value
    # FastAPI Query() returns a FieldInfo whose default is stored in .default
    default = getattr(value, "default", None)
    if isinstance(default, int):
        return default
    return fallback

# ---------------------------------------------------------------------------
# Cold-start: catalog + SentenceTransformer + AutoEncoder
# ---------------------------------------------------------------------------

catalog = get_catalog_from_s3()
mal_id_to_index = {anime["mal_id"]: i for i, anime in enumerate(catalog)}

# ---------------------------------------------------------------------------
# Cold-start: ANN RSS feed (cached per Lambda instance)
# ---------------------------------------------------------------------------
# Fetched once at module load so most requests pay zero latency.
# Lambda cold-start refreshes it automatically.
_ann_feed: Optional[Any] = None
_ann_feed_fetched_at: float = 0.0
_ANN_FEED_TTL = 3600  # seconds — refresh at most once per hour


def _get_ann_feed() -> Any:
    """Return a cached feedparser result, refreshing if stale."""
    global _ann_feed, _ann_feed_fetched_at
    now = time.time()
    if _ann_feed is None or (now - _ann_feed_fetched_at) > _ANN_FEED_TTL:
        try:
            _ann_feed = feedparser.parse(
                "https://www.animenewsnetwork.com/all/rss.xml"
            )
            _ann_feed_fetched_at = now
        except Exception as exc:
            print(f"[ann] RSS fetch error: {exc}")
            if _ann_feed is None:
                _ann_feed = feedparser.FeedParserDict()  # empty sentinel
    return _ann_feed


# Eagerly fetch at cold start (best-effort; won't crash startup on failure)
try:
    _get_ann_feed()
except Exception:
    pass


# ===========================================================================
# STATIC-PATH ROUTES — must come before /{mal_id} routes
# ===========================================================================

@router.get("/search")
def search_anime(q: str):
    """Substring search on catalog titles."""
    results = [anime for anime in catalog if q.lower() in (anime.get("title") or "").lower()]
    return {"results": results[:10]}


@router.get("/upcoming")
def get_upcoming_anime(per_page: int = Query(default=20, ge=1, le=50)):
    """
    Return a list of upcoming anime from AniList (falls back to Jikan).

    Uses the current UTC date to derive the relevant season and year.
    Results are cached locally in ``data/raw/upcoming_anime.json`` when
    S3_BUCKET_NAME is not set (local-dev mode).
    """
    # Guard: when called directly in tests, Query() objects are not resolved
    per_page = _resolve_query(per_page, 20)
    result = fetch_upcoming_anime(per_page=per_page)
    return result


class AnimeRecRequest(BaseModel):
    liked_ids: List[str]

@router.post("/recommendations")
def get_recommendations(request: AnimeRecRequest, limit: int = Query(default=10, ge=1, le=50)):
    """
    Return personalized anime recommendations based on a list of liked anime IDs.
    Constructs a 'taste vector' by averaging the latent embeddings of the liked anime,
    and returns the top-N most similar anime via cosine similarity.
    """
    if latent_matrix is None:
        raise HTTPException(status_code=500, detail="Anime embeddings not loaded")
        
    vectors = []
    valid_ids = []
    for aid in request.liked_ids:
        try:
            emb, _, _ = get_or_compute_embedding(int(aid))
            if emb is not None:
                vectors.append(emb)
                valid_ids.append(aid)
        except Exception as e:
            print(f"Error computing embedding for {aid}: {e}")
            
    if not valid_ids:
        return {"recommendations": []}
        
    # Create taste vector (average of liked anime embeddings)
    import numpy as np
    taste_vector = np.array(vectors).mean(axis=0, keepdims=True)
    
    # Compute cosine similarity using numpy
    norms = np.linalg.norm(latent_matrix, axis=1) * np.linalg.norm(taste_vector)
    similarities = np.dot(latent_matrix, taste_vector.T).flatten() / np.maximum(norms, 1e-6)
    
    # Get top N + len(valid_ids) to ensure we can exclude liked ones
    top_k = min(limit + len(valid_ids), len(similarities))
    if top_k >= len(similarities):
        top_indices = np.argsort(-similarities)
    else:
        top_indices = np.argpartition(-similarities, top_k)[:top_k]
        top_indices = top_indices[np.argsort(-similarities[top_indices])]
    
    recommendations = []
    liked_set = set(valid_ids)
    
    for idx in top_indices:
        idx = int(idx)
        score = similarities[idx]
        aid = latent_ids[idx]
        if aid in liked_set:
            continue
            
        data = anime_data_map[aid]
        recommendations.append({
            "id": aid,
            "title": data["title"],
            "imageUrl": data["imageUrl"],
            "reason": "Similar themes to your liked anime",
            "score": round(float(score), 4),
            "category": "anime"
        })
        
        if len(recommendations) == limit:
            break
            
    return {"recommendations": recommendations}


# ===========================================================================
# PARAMETERISED ROUTES — /{mal_id} and /{mal_id}/sub-paths
# ===========================================================================

@router.get("/{mal_id}")
def get_anime(mal_id: int):
    """Return a single anime record from the in-memory catalog."""
    if mal_id not in mal_id_to_index:
        raise HTTPException(status_code=404, detail="Anime not found in catalog")
    return catalog[mal_id_to_index[mal_id]]


@router.get("/{mal_id}/recommend")
def recommend_anime(
    mal_id: int,
    request: Request,
    n: int = 5,
    personalize: bool = Query(default=False),
):
    """
    Compute cosine similarity in the latent space of the AutoEncoder and
    return the top-N most similar anime from the catalog.

    Optional: pass ``?personalize=true`` to re-rank results using the user's
    cross-module taste profile (requires a valid session cookie).  The base
    similarity score is preserved — the profile boost only reorders; it never
    discards items.  Non-personalized behaviour is unchanged when the param
    is omitted or false.
    """
    from services.auth import serializer as _session_serializer
    user_id: Optional[str] = None
    _cookie = request.cookies.get("session")
    if _cookie:
        try:
            user_id = _session_serializer.loads(_cookie).get("user_id")
        except Exception:
            pass

    # First try to get or compute embedding
    embedding, title, genres = get_or_compute_embedding(mal_id)
    recommendations = []

    if embedding is not None:
        # We have a valid embedding
        import numpy as np
        seed_latent_cpu = np.array(embedding).reshape(1, -1)
        
        norms = np.linalg.norm(latent_matrix, axis=1) * np.linalg.norm(seed_latent_cpu)
        similarities = np.dot(latent_matrix, seed_latent_cpu.T).flatten() / np.maximum(norms, 1e-6)
        
        top_k = min(n + 1, len(similarities))
        if top_k >= len(similarities):
            top_indices = np.argsort(-similarities)
        else:
            top_indices = np.argpartition(-similarities, top_k)[:top_k]
            top_indices = top_indices[np.argsort(-similarities[top_indices])]
        
        for idx in top_indices:
            idx = int(idx)
            score = similarities[idx]
            aid = latent_ids[idx]
            if aid == str(mal_id):
                continue
            rec_anime = {
                "mal_id": int(aid),
                "title": anime_data_map[aid]["title"],
                "image_url": anime_data_map[aid].get("imageUrl", ""),
                "similarity_score": round(float(score), 4),
                "genres": anime_data_map[aid].get("genres", [])
            }
            recommendations.append(rec_anime)
            
            if len(recommendations) == n:
                break
    else:
        # Fallback to genre overlap for thin metadata
        if genres:
            seed_genres = set(g.lower() for g in genres)
            scored_candidates = []
            for aid in latent_ids:
                if aid == str(mal_id):
                    continue
                cand_genres = set(g.lower() for g in anime_data_map[aid].get('genres', []))
                if not cand_genres:
                    continue
                
                intersection = len(seed_genres.intersection(cand_genres))
                union = len(seed_genres.union(cand_genres))
                score = intersection / union if union > 0 else 0
                
                if score > 0:
                    scored_candidates.append((score, aid))
            
            scored_candidates.sort(reverse=True, key=lambda x: x[0])
            for score, aid in scored_candidates[:n]:
                rec_anime = {
                    "mal_id": int(aid),
                    "title": anime_data_map[aid]["title"],
                    "image_url": anime_data_map[aid].get("imageUrl", ""),
                    "similarity_score": round(score, 4),
                    "reason": "Based on genre similarity (thin metadata)",
                    "genres": anime_data_map[aid].get("genres", [])
                }
                recommendations.append(rec_anime)
        else:
            raise HTTPException(status_code=404, detail="Anime not found and no metadata available for fallback")

    # --- Optional: personalized re-ranking ---
    if personalize and user_id:
        try:
            from services.taste_profile import get_anime_boost_map  # lazy import
            boost_map = get_anime_boost_map(user_id)
            for rec in recommendations:
                rec_genres = [g.lower() for g in rec.get("genres", [])]
                genre_boost = sum(boost_map.get(g, 0.0) for g in rec_genres)
                # Boost formula: score * (1 + normalised_boost)
                # Normalise by dividing by 10 to keep multiplier sane
                normalised_boost = genre_boost / 10.0
                rec["personalized_score"] = round(
                    rec["similarity_score"] * (1.0 + normalised_boost), 4
                )
                rec["genre_boost"] = round(genre_boost, 4)
            # Re-sort by personalized_score
            recommendations.sort(key=lambda r: r["personalized_score"], reverse=True)
        except Exception as exc:
            print(f"[anime] personalize error: {exc}")
            # Fall through — return un-boosted results

    return {"recommendations": recommendations, "personalized": personalize}


@router.get("/{mal_id}/reviews")
def get_anime_reviews(mal_id: int, per_page: int = Query(default=5, ge=1, le=20)):
    """
    Return review snippets, scores, and reviewer usernames for the given anime.

    Uses AniList's ``idMal`` field to look up by MAL ID without a separate
    ID-translation step.  Falls back to Jikan's /anime/{id}/reviews if
    AniList is unreachable.
    """
    per_page = _resolve_query(per_page, 5)
    result = fetch_reviews_by_mal_id(mal_id=mal_id, per_page=per_page)
    if result.get("source") == "error":
        raise HTTPException(
            status_code=503,
            detail="Could not fetch reviews from AniList or Jikan. Try again later.",
        )
    return result


@router.get("/{mal_id}/videos")
def get_anime_videos(mal_id: int, max_results: int = Query(default=5, ge=1, le=10)):
    """
    Search YouTube for trailers and explainer videos for the given anime.

    Requires the YOUTUBE_API_KEY environment variable (YouTube Data API v3).
    Returns only video_id, title, channel, and thumbnail — the frontend
    embeds the YouTube player client-side; no video content is proxied.

    Note: YouTube Data API v3 search.list costs 100 quota units per call.
    The free tier provides 10,000 units/day (~100 searches/day).
    """
    max_results = _resolve_query(max_results, 5)
    if not YOUTUBE_API_KEY:
        # Return empty list gracefully instead of 503 so frontend doesn't break
        return {
            "mal_id": mal_id,
            "anime_title": "",
            "query": "",
            "videos": [],
        }

    if mal_id in mal_id_to_index:
        anime_title = catalog[mal_id_to_index[mal_id]].get("title", "")
    elif str(mal_id) in anime_data_map:
        anime_title = anime_data_map[str(mal_id)].get("title", "")
    else:
        raise HTTPException(status_code=404, detail="Anime not found")

    search_query = f"{anime_title} explained OR trailer OR PV"

    try:
        response = requests.get(
            YOUTUBE_SEARCH_URL,
            params={
                "part": "snippet",
                "q": search_query,
                "type": "video",
                "order": "relevance",
                "maxResults": max_results,
                "key": YOUTUBE_API_KEY,
            },
            timeout=8,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"YouTube API request failed: {exc}",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"YouTube API error: {response.text[:200]}",
        )

    items = response.json().get("items", [])
    videos = [
        {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "thumbnail": item["snippet"]["thumbnails"].get("medium", {}).get("url"),
        }
        for item in items
        if item.get("id", {}).get("videoId")
    ]

    return {
        "mal_id": mal_id,
        "anime_title": anime_title,
        "query": search_query,
        "videos": videos,
    }


@router.get("/{mal_id}/news")
def get_anime_news(mal_id: int, max_articles: int = Query(default=10, ge=1, le=25)):
    """
    Return Anime News Network RSS articles whose title or summary contains
    the anime's catalog title (case-insensitive substring match).

    The RSS feed is cached in-memory per Lambda instance (TTL: 1 hour) so
    most requests pay zero network latency.  No API key required.
    """
    max_articles = _resolve_query(max_articles, 10)
    
    if mal_id in mal_id_to_index:
        anime_title = catalog[mal_id_to_index[mal_id]].get("title", "")
    elif str(mal_id) in anime_data_map:
        anime_title = anime_data_map[str(mal_id)].get("title", "")
    else:
        raise HTTPException(status_code=404, detail="Anime not found")

    title_lower = anime_title.lower()

    feed = _get_ann_feed()
    entries = getattr(feed, "entries", [])

    articles = []
    for entry in entries:
        entry_title = (entry.get("title") or "").lower()
        entry_summary = (entry.get("summary") or "").lower()
        if title_lower in entry_title or title_lower in entry_summary:
            articles.append(
                {
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "published": entry.get("published"),
                    "summary": (entry.get("summary") or "")[:300].rstrip()
                    + ("…" if len(entry.get("summary") or "") > 300 else ""),
                }
            )
        if len(articles) >= max_articles:
            break

    return {
        "mal_id": mal_id,
        "anime_title": anime_title,
        "articles": articles,
    }


# ===========================================================================
# LIKE / UNLIKE — authenticated, personalised signal collection
# ===========================================================================

@router.post("/{mal_id}/like", status_code=status.HTTP_201_CREATED)
def like_anime(mal_id: int, user_id: str = Depends(get_current_user_id)):
    """Record that the authenticated user liked this anime."""
    if mal_id not in mal_id_to_index:
        raise HTTPException(status_code=404, detail="Anime not found in catalog")
    add_like(user_id, "anime", str(mal_id))
    return {"liked": True, "mal_id": mal_id}


@router.delete("/{mal_id}/like", status_code=status.HTTP_200_OK)
def unlike_anime(mal_id: int, user_id: str = Depends(get_current_user_id)):
    """Remove a previously liked anime for the authenticated user."""
    remove_like(user_id, "anime", str(mal_id))
    return {"liked": False, "mal_id": mal_id}
