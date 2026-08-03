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
PLACES_API_BASE_URL = "https://places.googleapis.com/v1"

PRICE_LEVEL_MAP = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4
}

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
    Search for restaurants using the Places API (New) Text Search endpoint.
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

    headers = {
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.types,places.priceLevel,places.rating,places.photos",
        "Content-Type": "application/json"
    }

    payload: Dict[str, Any] = {
        "textQuery": f"{query} in {location}" if location else query,
        "includedType": "restaurant"
    }
    if lat is not None and lon is not None:
        payload["locationBias"] = {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": 5000.0
            }
        }

    try:
        response = requests.post(
            f"{PLACES_API_BASE_URL}/places:searchText",
            headers=headers,
            json=payload,
            timeout=8
        )
        if response.status_code == 200:
            data = response.json()
            places = data.get("places", [])
            
            parsed_results = []
            for item in places:
                photo_ref = None
                if item.get("photos"):
                    photo_name = item["photos"][0].get("name")
                    if photo_name:
                        photo_ref = photo_name.split("/")[-1]
                        
                pl = item.get("priceLevel")
                mapped_price = PRICE_LEVEL_MAP.get(pl) if pl else None
                    
                parsed_results.append({
                    "place_id": item.get("id"),
                    "name": item.get("displayName", {}).get("text"),
                    "types": item.get("types", []),
                    "rating": item.get("rating"),
                    "price_level": mapped_price,
                    "address": item.get("formattedAddress"),
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
    Get full details for a single restaurant using the Place Details (New) endpoint.
    Caches results for 1 hour.
    """
    if not GOOGLE_PLACES_API_KEY:
        print("[places] GOOGLE_PLACES_API_KEY is not set.")
        return None

    now = time.time()
    if place_id in _details_cache and (now - _details_fetched_at.get(place_id, 0)) <= _DETAILS_TTL:
        return _details_cache[place_id]

    headers = {
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "id,displayName,types,rating,priceLevel,formattedAddress,photos,editorialSummary,websiteUri,location"
    }

    try:
        response = requests.get(
            f"{PLACES_API_BASE_URL}/places/{place_id}",
            headers=headers,
            timeout=8
        )
        if response.status_code == 200:
            result = response.json()
                
            photo_ref = None
            if result.get("photos"):
                photo_name = result["photos"][0].get("name")
                if photo_name:
                    photo_ref = photo_name.split("/")[-1]
                
            summary = None
            if result.get("editorialSummary"):
                summary = result["editorialSummary"].get("text")
                
            location = None
            if result.get("location"):
                location = {
                    "lat": result["location"].get("latitude"),
                    "lng": result["location"].get("longitude")
                }
                
            pl = result.get("priceLevel")
            mapped_price = PRICE_LEVEL_MAP.get(pl) if pl else None

            parsed = {
                "place_id": result.get("id"),
                "name": result.get("displayName", {}).get("text"),
                "types": result.get("types", []),
                "rating": result.get("rating"),
                "price_level": mapped_price,
                "address": result.get("formattedAddress"),
                "photo_reference": photo_ref,
                "summary": summary,
                "url": result.get("websiteUri"),
                "location": location
            }
            
            _details_cache[place_id] = parsed
            _details_fetched_at[place_id] = now
            return parsed
            
        print(f"[places] details HTTP {response.status_code}: {response.text[:200]}")
    except Exception as exc:
        print(f"[places] details error: {exc}")
        
    return None
