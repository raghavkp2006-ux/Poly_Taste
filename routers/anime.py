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
import torch
import torch.nn as nn
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from sklearn.feature_extraction.text import TfidfVectorizer

from models.anime_dnn import AnimeAutoEncoder
from services.anilist_client import fetch_reviews_by_mal_id, fetch_upcoming_anime
from services.jikan_client import get_catalog_from_s3

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
# Cold-start: catalog + TF-IDF + AutoEncoder (unchanged)
# ---------------------------------------------------------------------------

catalog = get_catalog_from_s3()
mal_id_to_index = {anime["mal_id"]: i for i, anime in enumerate(catalog)}

tf_idf_matrix = None
vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")

if catalog:
    texts = [
        f"{anime.get('synopsis', '')} {' '.join(anime.get('genres', []))}"
        for anime in catalog
    ]
    tf_idf_matrix = vectorizer.fit_transform(texts).toarray()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
anime_model = AnimeAutoEncoder(input_dim=1000, latent_dim=32).to(device)

_model_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "models",
    "anime_model.pth",
)
if os.path.exists(_model_path):
    anime_model.load_state_dict(torch.load(_model_path, map_location=device))
anime_model.eval()

latent_catalog = None
if tf_idf_matrix is not None:
    with torch.no_grad():
        tf_idf_tensor = torch.tensor(tf_idf_matrix, dtype=torch.float32).to(device)
        latent_catalog = anime_model.encode(tf_idf_tensor)

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
def recommend_anime(mal_id: int, n: int = 5):
    """
    Compute cosine similarity in the latent space of the AutoEncoder and
    return the top-N most similar anime from the catalog.
    """
    if mal_id not in mal_id_to_index:
        raise HTTPException(status_code=404, detail="Anime not found in catalog")

    if latent_catalog is None:
        raise HTTPException(status_code=500, detail="Model or catalog not properly loaded")

    seed_idx = mal_id_to_index[mal_id]
    seed_latent = latent_catalog[seed_idx].unsqueeze(0)  # (1, 32)

    cos = nn.CosineSimilarity(dim=1, eps=1e-6)
    similarities = cos(seed_latent, latent_catalog)  # (N,)

    scores, indices = torch.topk(similarities, n + 1)

    recommendations = []
    for score, idx in zip(scores, indices):
        idx = idx.item()
        if idx == seed_idx:
            continue
        rec_anime = catalog[idx].copy()
        rec_anime["similarity_score"] = round(score.item(), 4)
        recommendations.append(rec_anime)

        if len(recommendations) == n:
            break

    return {"recommendations": recommendations}


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
        raise HTTPException(
            status_code=503,
            detail=(
                "YOUTUBE_API_KEY is not configured. "
                "Set it in your .env file to enable video search."
            ),
        )

    if mal_id not in mal_id_to_index:
        raise HTTPException(status_code=404, detail="Anime not found in catalog")

    anime_title = catalog[mal_id_to_index[mal_id]].get("title", "")
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
    if mal_id not in mal_id_to_index:
        raise HTTPException(status_code=404, detail="Anime not found in catalog")

    anime_title = catalog[mal_id_to_index[mal_id]].get("title") or ""
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
