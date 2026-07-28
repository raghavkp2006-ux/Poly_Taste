"""
services/google_places_client.py — Google Places API client for Restaurants.

Wraps the Places API for text search and place details.
Includes a short in-memory TTL cache to prevent duplicate network calls
within a Lambda instance's lifetime, conserving quota.
"""

import os
import time
from typing import Any, Dict, List, Optional

import requests

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
PLACES_API_BASE_URL = "https://maps.googleapis.com/maps/api/place"

# ---------------------------------------------------------------------------
# In-Memory Cache (TTL)
# ---------------------------------------------------------------------------

_search_cache: Dict[str, Dict[str, Any]] = {}
_search_fetched_at: Dict[str, float] = {}
_SEARCH_TTL = 3600  # 1 hour

_details_cache: Dict[str, Dict[str, Any]] = {}
_details_fetched_at: Dict[str, float] = {}
_DETAILS_TTL = 3600  # 1 hour

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_restaurants(
    query: str, 
    location: Optional[str] = None, 
    lat: Optional[float] = None, 
    lon: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Search for restaurants using the Places API Text Search endpoint.
    Caches results for 1 hour based on the exact query parameters.
    """
    if not GOOGLE_PLACES_API_KEY:
        print("[places] GOOGLE_PLACES_API_KEY is not set.")
        return []

    # Build cache key
    cache_key = f"{query}|{location}|{lat}|{lon}"
    now = time.time()
    if cache_key in _search_cache and (now - _search_fetched_at.get(cache_key, 0)) <= _SEARCH_TTL:
        return _search_cache[cache_key]

    # Build request params
    params: Dict[str, Any] = {
        "query": query,
        "type": "restaurant",
        "key": GOOGLE_PLACES_API_KEY
    }
    
    if location:
        params["query"] = f"{query} in {location}"
    elif lat is not None and lon is not None:
        params["location"] = f"{lat},{lon}"
        # A radius is usually required when location is provided for textsearch
        params["radius"] = 5000 

    try:
        response = requests.get(
            f"{PLACES_API_BASE_URL}/textsearch/json",
            params=params,
            timeout=8
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            parsed_results = []
            for item in results:
                photo_ref = None
                if item.get("photos"):
                    photo_ref = item["photos"][0].get("photo_reference")
                    
                parsed_results.append({
                    "place_id": item.get("place_id"),
                    "name": item.get("name"),
                    "types": item.get("types", []),
                    "rating": item.get("rating"),
                    "price_level": item.get("price_level"),
                    "address": item.get("formatted_address"),
                    "photo_reference": photo_ref
                })
            
            _search_cache[cache_key] = parsed_results
            _search_fetched_at[cache_key] = now
            return parsed_results
            
        print(f"[places] textsearch HTTP {response.status_code}: {response.text[:200]}")
    except Exception as exc:
        print(f"[places] textsearch error: {exc}")
        
    return []

def get_restaurant_details(place_id: str) -> Optional[Dict[str, Any]]:
    """
    Get full details for a single restaurant using the Place Details endpoint.
    Caches results for 1 hour.
    """
    if not GOOGLE_PLACES_API_KEY:
        print("[places] GOOGLE_PLACES_API_KEY is not set.")
        return None

    now = time.time()
    if place_id in _details_cache and (now - _details_fetched_at.get(place_id, 0)) <= _DETAILS_TTL:
        return _details_cache[place_id]

    try:
        response = requests.get(
            f"{PLACES_API_BASE_URL}/details/json",
            params={
                "place_id": place_id,
                "fields": "place_id,name,types,rating,price_level,formatted_address,photos,editorial_summary,url,geometry",
                "key": GOOGLE_PLACES_API_KEY
            },
            timeout=8
        )
        if response.status_code == 200:
            data = response.json()
            result = data.get("result")
            if not result:
                return None
                
            photo_ref = None
            if result.get("photos"):
                photo_ref = result["photos"][0].get("photo_reference")
                
            summary = None
            if result.get("editorial_summary"):
                summary = result["editorial_summary"].get("overview")
                
            location = None
            if result.get("geometry") and result["geometry"].get("location"):
                location = result["geometry"]["location"]
                
            parsed = {
                "place_id": result.get("place_id"),
                "name": result.get("name"),
                "types": result.get("types", []),
                "rating": result.get("rating"),
                "price_level": result.get("price_level"),
                "address": result.get("formatted_address"),
                "photo_reference": photo_ref,
                "summary": summary,
                "url": result.get("url"),
                "location": location
            }
            
            _details_cache[place_id] = parsed
            _details_fetched_at[place_id] = now
            return parsed
            
        print(f"[places] details HTTP {response.status_code}: {response.text[:200]}")
    except Exception as exc:
        print(f"[places] details error: {exc}")
        
    return None
