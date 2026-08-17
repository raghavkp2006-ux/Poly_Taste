"""
services/google_places_client.py — Geoapify API client for Restaurants.

Wraps the Geoapify Places and Geocoding APIs for text search, place details,
and category-based discovery, mapped to Google Places style properties for
compatibility.
"""

import os
import time
from typing import Any, Dict, List, Optional
import requests

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", os.getenv("GOOGLE_PLACES_API_KEY"))

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
# Beautiful Unsplash Images mapping for Cuisines (to ensure stunning UI)
# ---------------------------------------------------------------------------

CUISINE_IMAGE_MAP = {
    "italian_restaurant": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=400&q=80",
    "pizza_restaurant": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=400&q=80",
    "japanese_restaurant": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=400&q=80",
    "sushi_restaurant": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=400&q=80",
    "ramen_restaurant": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=400&q=80",
    "mexican_restaurant": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=400&q=80",
    "hamburger_restaurant": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=400&q=80",
    "seafood_restaurant": "https://images.unsplash.com/photo-1534080391025-09795d197a5b?auto=format&fit=crop&w=400&q=80",
    "bakery": "https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=400&q=80",
    "dessert_shop": "https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=400&q=80",
    "ice_cream_shop": "https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=400&q=80",
    "dessert_restaurant": "https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=400&q=80",
    "coffee_shop": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=400&q=80",
    "cafe": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=400&q=80",
    "fine_dining_restaurant": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=400&q=80",
    "mediterranean_restaurant": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=400&q=80",
    "french_restaurant": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=400&q=80"
}
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=400&q=80"

def get_image_for_types(types: List[str]) -> str:
    for t in types:
        if t in CUISINE_IMAGE_MAP:
            return CUISINE_IMAGE_MAP[t]
    return DEFAULT_IMAGE

# ---------------------------------------------------------------------------
# Mapping Utilities (Geoapify <-> Google Places format)
# ---------------------------------------------------------------------------

def map_categories_to_types(categories: List[str]) -> List[str]:
    """Map Geoapify categories back to Google Places types for compatibility."""
    types = ["restaurant", "food"]
    for cat in categories:
        cat = cat.lower()
        if "catering.restaurant.italian" in cat:
            types.append("italian_restaurant")
        elif "catering.restaurant.japanese" in cat:
            types.append("japanese_restaurant")
        elif "catering.restaurant.mexican" in cat:
            types.append("mexican_restaurant")
        elif "catering.restaurant.korean" in cat:
            types.append("korean_restaurant")
        elif "catering.restaurant.french" in cat:
            types.append("french_restaurant")
        elif "catering.restaurant.ramen" in cat:
            types.append("ramen_restaurant")
        elif "catering.restaurant.vegetarian" in cat:
            types.append("vegetarian_restaurant")
        elif "catering.restaurant.vegan" in cat:
            types.append("vegan_restaurant")
        elif "catering.restaurant.sushi" in cat:
            types.append("sushi_restaurant")
        elif "catering.restaurant.pizza" in cat:
            types.append("pizza_restaurant")
        elif "catering.restaurant.hamburger" in cat:
            types.append("hamburger_restaurant")
        elif "catering.restaurant.seafood" in cat:
            types.append("seafood_restaurant")
        elif "catering.restaurant.mediterranean" in cat:
            types.append("mediterranean_restaurant")
        elif "catering.restaurant.brunch" in cat:
            types.append("brunch_restaurant")
        elif "catering.restaurant.fine_dining" in cat:
            types.append("fine_dining_restaurant")
        elif "catering.restaurant.fusion" in cat:
            types.append("fusion_restaurant")
        elif "catering.restaurant.thai" in cat:
            types.append("thai_restaurant")
        elif "catering.fast_food" in cat:
            types.append("fast_food_restaurant")
        elif "catering.cafe" in cat:
            types.append("cafe")
            types.append("coffee_shop")
        elif "catering.bar" in cat:
            types.append("bar")
        elif "catering.pub" in cat:
            types.append("pub")
        elif "catering.bakery" in cat:
            types.append("bakery")
        elif "catering.ice_cream" in cat:
            types.append("ice_cream_shop")

    # Also support general matching of catering.restaurant.*
    for cat in categories:
        if cat.startswith("catering.restaurant."):
            cuisine = cat.split(".")[-1]
            types.append(f"{cuisine}_restaurant")

    return list(dict.fromkeys(types))

def map_query_to_categories(query: str) -> List[str]:
    """Identify if the search query contains category or cuisine keywords."""
    words = query.lower().replace("_", " ").split()
    categories = []
    
    for w in words:
        if w in ["italian", "pizza"]:
            categories.extend(["catering.restaurant.italian", "catering.restaurant.pizza"])
        elif w in ["japanese", "sushi", "ramen"]:
            categories.extend(["catering.restaurant.japanese", "catering.restaurant.sushi", "catering.restaurant.ramen"])
        elif w == "mexican":
            categories.append("catering.restaurant.mexican")
        elif w == "korean":
            categories.append("catering.restaurant.korean")
        elif w == "french":
            categories.append("catering.restaurant.french")
        elif w == "thai":
            categories.append("catering.restaurant.thai")
        elif w == "seafood":
            categories.append("catering.restaurant.seafood")
        elif w in ["burger", "hamburger"]:
            categories.append("catering.restaurant.hamburger")
        elif w == "mediterranean":
            categories.append("catering.restaurant.mediterranean")
        elif w in ["cafe", "coffee"]:
            categories.append("catering.cafe")
        elif w in ["bar", "pub"]:
            categories.extend(["catering.bar", "catering.pub"])
        elif w in ["bakery", "dessert"]:
            categories.append("catering.bakery")
        elif w in ["fast", "fast_food"]:
            categories.append("catering.fast_food")
            
    if not categories:
        if any(kw in words for kw in ["restaurant", "restaurants", "food", "eat", "dining"]):
            categories.append("catering.restaurant")
            
    return list(set(categories))

def geocode_location(location: str) -> Optional[tuple[float, float]]:
    """Geocode a text location to get latitude and longitude."""
    if not GEOAPIFY_API_KEY:
        return None
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": location,
        "apiKey": GEOAPIFY_API_KEY,
        "limit": 1
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            features = resp.json().get("features", [])
            if features:
                props = features[0].get("properties", {})
                lat_val = props.get("lat")
                lon_val = props.get("lon")
                if lat_val is not None and lon_val is not None:
                    return float(lat_val), float(lon_val)
    except Exception as e:
        print(f"[geocode] Error geocoding location {location}: {e}")
    return None

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
    Search for restaurants using Geoapify Places (category search) or Geocoding (text search).
    """
    if not GEOAPIFY_API_KEY:
        print("[places] GEOAPIFY_API_KEY is not set.")
        return []

    cache_key = f"{query}|{location}|{lat}|{lon}"
    now = time.time()
    if cache_key in _search_cache and (now - _search_fetched_at.get(cache_key, 0)) <= _SEARCH_TTL:
        return _search_cache[cache_key]

    if (lat is None or lon is None) and location:
        resolved = geocode_location(location)
        if resolved:
            lat, lon = resolved

    params: Dict[str, Any] = {
        "apiKey": GEOAPIFY_API_KEY,
        "limit": 20
    }

    categories = map_query_to_categories(query)
    use_places_api = categories and (lat is not None and lon is not None)

    if use_places_api:
        url = "https://api.geoapify.com/v2/places"
        params["categories"] = ",".join(categories)
        params["filter"] = f"circle:{lon},{lat},5000"
        params["bias"] = f"proximity:{lon},{lat}"
    else:
        url = "https://api.geoapify.com/v1/geocode/search"
        text_query = f"{query}, {location}" if location else query
        params["text"] = text_query
        if lat is not None and lon is not None:
            params["filter"] = f"circle:{lon},{lat},5000"
            params["bias"] = f"proximity:{lon},{lat}"

    try:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            
            parsed_results = []
            for feat in features:
                props = feat.get("properties", {})
                cats = props.get("categories", [])
                mapped_types = map_categories_to_types(cats)
                photo_url = get_image_for_types(mapped_types)
                
                parsed_results.append({
                    "place_id": props.get("place_id"),
                    "name": props.get("name") or props.get("formatted", "Restaurant"),
                    "types": mapped_types,
                    "rating": 4.0,  # Fallback rating
                    "price_level": None,  # Price level mapping fallback
                    "address": props.get("formatted") or props.get("address_line2"),
                    "photo_reference": photo_url
                })
            
            _search_cache[cache_key] = parsed_results
            _search_fetched_at[cache_key] = now
            return parsed_results
            
    except Exception as exc:
        print(f"[places] search error: {exc}")
        
    return []

def get_restaurant_details(place_id: str) -> Optional[Dict[str, Any]]:
    """
    Get full details for a single restaurant using the Geoapify Place Details API.
    """
    if not GEOAPIFY_API_KEY:
        print("[places] GEOAPIFY_API_KEY is not set.")
        return None

    now = time.time()
    if place_id in _details_cache and (now - _details_fetched_at.get(place_id, 0)) <= _DETAILS_TTL:
        return _details_cache[place_id]

    url = "https://api.geoapify.com/v2/place-details"
    params = {
        "id": place_id,
        "apiKey": GEOAPIFY_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            if not features:
                return None
                
            feat = features[0]
            props = feat.get("properties", {})
            cats = props.get("categories", [])
            mapped_types = map_categories_to_types(cats)
            
            lat_val = props.get("lat")
            lon_val = props.get("lon")
            location_dict = None
            if lat_val is not None and lon_val is not None:
                location_dict = {
                    "lat": float(lat_val),
                    "lng": float(lon_val)
                }
                
            photo_url = get_image_for_types(mapped_types)
            
            cuisine_types = [t.replace('_restaurant', '') for t in mapped_types if t not in ['restaurant', 'food']]
            summary = props.get("description") or f"A wonderful restaurant serving {', '.join(cuisine_types)}." if cuisine_types else "A wonderful local dining option."

            parsed = {
                "place_id": props.get("place_id") or place_id,
                "name": props.get("name") or props.get("formatted", "Restaurant"),
                "types": mapped_types,
                "rating": 4.0,
                "price_level": None,
                "address": props.get("formatted") or props.get("address_line2"),
                "photo_reference": photo_url,
                "summary": summary,
                "url": props.get("website") or props.get("contact", {}).get("website"),
                "location": location_dict
            }
            
            _details_cache[place_id] = parsed
            _details_fetched_at[place_id] = now
            return parsed
            
    except Exception as exc:
        print(f"[places] details error: {exc}")
        
    return None
