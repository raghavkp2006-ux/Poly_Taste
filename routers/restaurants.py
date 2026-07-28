"""
routers/restaurants.py — Restaurant recommendation module.

Endpoints
---------
  GET /restaurants/search?q=&location=     — Text search via Google Places API
  GET /restaurants/{place_id}              — Place Details
  GET /restaurants/{place_id}/recommend    — Similar restaurants via TF-IDF (content-similarity)
"""

from typing import Any, Dict, List, Optional
import numpy as np

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import add_like, remove_like
from services.auth import get_current_user_id
from services.google_places_client import search_restaurants, get_restaurant_details

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

def _resolve_query(value: Any, fallback: int) -> int:
    """Helper for testing (FastAPI Query resolution)"""
    if isinstance(value, int):
        return value
    default = getattr(value, "default", None)
    if isinstance(default, int):
        return default
    return fallback

# ===========================================================================
# STATIC-PATH ROUTES
# ===========================================================================

@router.get("/search")
def search_restaurants_endpoint(
    q: str = Query(..., min_length=1),
    location: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
):
    """
    Search for restaurants using the Google Places API.
    """
    results = search_restaurants(query=q, location=location, lat=lat, lon=lon)
    return {"results": results[:20]}


# ===========================================================================
# PARAMETERISED ROUTES
# ===========================================================================

@router.get("/{place_id}")
def get_restaurant(place_id: str):
    """
    Get full details for a restaurant via Google Places API.
    """
    restaurant = get_restaurant_details(place_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.get("/{place_id}/recommend")
def recommend_restaurants(
    place_id: str,
    request: Request,
    n: int = Query(default=5, ge=1, le=20),
    personalize: bool = Query(default=False),
):
    """
    Find similar restaurants using TF-IDF cosine similarity.
    Since we don't have a static catalog, this searches for restaurants nearby the seed
    and ranks them based on cuisine (types) and price_level similarity.
    """
    n = _resolve_query(n, 5)
    
    # 1. Get seed restaurant
    seed_restaurant = get_restaurant_details(place_id)
    if not seed_restaurant:
        raise HTTPException(status_code=404, detail="Seed restaurant not found")
        
    lat = None
    lon = None
    if seed_restaurant.get("location"):
        lat = seed_restaurant["location"].get("lat")
        lon = seed_restaurant["location"].get("lng")
        
    # 2. Find candidate restaurants nearby (using the types of the seed to constrain search)
    seed_types = [t for t in seed_restaurant.get("types", []) if t not in ["restaurant", "food", "point_of_interest", "establishment"]]
    query = " ".join(seed_types) if seed_types else "restaurant"
    
    # We fetch a larger pool to rank
    candidates = search_restaurants(query=query, lat=lat, lon=lon)
    
    # Make sure seed is included in candidates for vectorization, but we don't add duplicates
    all_places = {place_id: seed_restaurant}
    for c in candidates:
        all_places[c["place_id"]] = c
        
    catalog = list(all_places.values())
    if len(catalog) <= 1:
        return {"place_id": place_id, "seed_name": seed_restaurant.get("name"), "recommendations": []}
        
    # 3. Build TF-IDF matrix based on types and price level
    texts = []
    for p in catalog:
        # types
        t = " ".join(p.get("types", []))
        # price level (give it some weight)
        pl = f"price_{p.get('price_level', 'unknown')} " * 3
        texts.append(f"{t} {pl}")
        
    vectorizer = TfidfVectorizer(max_features=100)
    tfidf_matrix = vectorizer.fit_transform(texts).toarray()
    
    # 4. Compute cosine similarity
    seed_idx = next(i for i, p in enumerate(catalog) if p["place_id"] == place_id)
    seed_vec = tfidf_matrix[seed_idx].reshape(1, -1)
    
    sims = cosine_similarity(seed_vec, tfidf_matrix)[0]
    
    top_indices = np.argsort(sims)[::-1]
    
    recommendations = []
    for idx in top_indices:
        if int(idx) == seed_idx:
            continue
        rec = catalog[idx].copy()
        rec["similarity_score"] = round(float(sims[idx]), 4)
        recommendations.append(rec)
        if len(recommendations) >= n:
            break

    # 5. Personalize (optional)
    if personalize:
        user_id = None
        _cookie = request.cookies.get("session")
        if _cookie:
            from services.auth import serializer as _session_serializer
            try:
                user_id = _session_serializer.loads(_cookie).get("user_id")
            except Exception:
                pass
                
        if user_id:
            try:
                from services.taste_profile import get_restaurant_boost_map
                boost_map = get_restaurant_boost_map(user_id)
                
                for rec in recommendations:
                    rec_types = [t.lower() for t in rec.get("types", [])]
                    type_boost = sum(boost_map.get(t, 0.0) for t in rec_types)
                    
                    normalised_boost = type_boost / 10.0
                    rec["personalized_score"] = round(
                        rec["similarity_score"] * (1.0 + normalised_boost), 4
                    )
                    rec["cuisine_boost"] = round(type_boost, 4)
                
                recommendations.sort(key=lambda r: r.get("personalized_score", r["similarity_score"]), reverse=True)
            except Exception as exc:
                print(f"[restaurants] personalize error: {exc}")

    return {
        "place_id": place_id,
        "seed_name": seed_restaurant.get("name"),
        "recommendations": recommendations,
        "personalized": personalize
    }


# ===========================================================================
# LIKE / UNLIKE
# ===========================================================================

@router.post("/{place_id}/like", status_code=status.HTTP_201_CREATED)
def like_restaurant(place_id: str, user_id: str = Depends(get_current_user_id)):
    """Record that the authenticated user liked this restaurant."""
    # Verify it exists
    if not get_restaurant_details(place_id):
        raise HTTPException(status_code=404, detail="Restaurant not found")
    # use "restaurants" as module string
    add_like(user_id, "restaurants", place_id)
    return {"liked": True, "place_id": place_id}


@router.delete("/{place_id}/like", status_code=status.HTTP_200_OK)
def unlike_restaurant(place_id: str, user_id: str = Depends(get_current_user_id)):
    """Remove a previously liked restaurant for the authenticated user."""
    remove_like(user_id, "restaurants", place_id)
    return {"liked": False, "place_id": place_id}
