"""
routers/movie.py — Movie domain router.

Endpoints
---------
Static paths (registered first):
  GET  /movie/search                 — substring search on movie titles
  POST /movie/recommendations        — personalized multi-item or auto-seeded recommendations

Parameterised paths:
  GET  /movie/{movie_id}             — single movie detail
  GET  /movie/{movie_id}/recommend   — TF-IDF cosine similarity recommendations
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.movie_recommender import (
    get_similar_movies,
    get_taste_vector_recommendations,
    movie_data_map,
    movie_ids,
    _resolve_movie_index,
)

router = APIRouter(prefix="/movie", tags=["movie"])


class MovieRecRequest(BaseModel):
    liked_ids: Optional[List[str]] = None


# ===========================================================================
# STATIC-PATH ROUTES — registered BEFORE parameterised routes
# ===========================================================================

@router.get("/search")
def search_movies(q: str = Query(..., min_length=1)):
    """Substring search on catalog movie titles."""
    q_lower = q.lower()
    results = [
        meta for meta in movie_data_map.values()
        if q_lower in (meta.get("title") or "").lower()
    ]
    return {"results": results[:10]}


@router.post("/recommendations")
def get_recommendations(
    request: MovieRecRequest,
    n: int = Query(default=10, ge=1, le=50),
):
    """
    Return personalized movie recommendations.
    - If liked_ids provided in body: average TF-IDF vectors of liked movies.
    - If liked_ids empty/omitted: auto-seed using movies with personal_rating >= 7.0
      weighted by (personal_rating - 5.5).
    """
    recommendations = get_taste_vector_recommendations(liked_ids=request.liked_ids, n=n)
    return {"recommendations": recommendations}


# ===========================================================================
# PARAMETERISED ROUTES — /{movie_id} and sub-paths
# ===========================================================================

@router.get("/{movie_id}")
def get_movie(movie_id: str):
    """Return a single movie record from catalog by tmdb_id or database id."""
    idx = _resolve_movie_index(movie_id)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Movie '{movie_id}' not found in catalog")

    tmdb_id_str = movie_ids[idx]
    return movie_data_map.get(tmdb_id_str, {})


@router.get("/{movie_id}/recommend")
def recommend_movie(
    movie_id: str,
    n: int = Query(default=5, ge=1, le=50),
):
    """
    Compute TF-IDF cosine similarity against the precomputed catalog matrix
    and return top-N most similar movies matching the shared contract:
    { id, title, imageUrl, reason, score, category: "movie" }.
    """
    idx = _resolve_movie_index(movie_id)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Movie '{movie_id}' not found in catalog")

    recommendations = get_similar_movies(movie_id=movie_id, n=n)
    return {"recommendations": recommendations}
