"""
services/taste_profile.py — Cross-module taste profile engine.

compute_taste_profile(user_id, spotify_token=None) aggregates signal from:
  1. Spotify   — weighted genre profile from top artists (reuses compute_genre_profile
                 from routers.spotify — no duplication)
  2. Anime     — genres of explicitly liked anime entries
  3. Restaurants — types/cuisines of explicitly liked restaurants

The three signal vectors are merged into a single {keyword: float} dict.
A genre crosswalk maps Spotify music genres to semantically related anime
genres, and music/anime genres to restaurant cuisines.
"""

from __future__ import annotations

import requests
from typing import Any, Dict, List, Optional

from database import get_likes, get_anilist_user
from services.anilist_client import fetch_user_anime_list

# ---------------------------------------------------------------------------
# Genre crosswalk: Spotify music genre → related anime genre keywords
# These are the seeds for the ?personalize=true boost in routers/anime.py.
# ---------------------------------------------------------------------------
GENRE_CROSSWALK: Dict[str, List[str]] = {
    # High-energy music → high-energy anime
    "rock": ["action", "shonen", "adventure"],
    "metal": ["action", "shonen", "dark fantasy", "seinen"],
    # Chill / jazz → slice-of-life, drama
    "jazz": ["slice of life", "drama", "music", "josei"],
    "classical": ["slice of life", "drama", "music"],
    "ambient": ["slice of life", "psychological", "drama"],
    # Electronic → futuristic / cerebral
    "electronic": ["sci-fi", "mecha", "psychological"],
    # Pop / indie → romance / comedy
    "pop": ["romance", "comedy", "school"],
    "indie": ["romance", "slice of life", "comedy"],
    # Hip-hop / rap → sports, street
    "hip hop": ["sports", "action", "adventure"],
    "rap": ["sports", "action"],
    # Country / folk → historical / rural
    "country": ["historical", "adventure", "fantasy"],
    "folk": ["historical", "fantasy"],
    # R&B → romance
    "r&b": ["romance", "drama", "music"],
}

# ---------------------------------------------------------------------------
# Cuisine crosswalk: Music/Anime genre → Restaurant Cuisine types
# ---------------------------------------------------------------------------
CUISINE_CROSSWALK: Dict[str, List[str]] = {
    # High-energy music/anime → street food, fast casual, spicy
    "rock": ["meal_takeaway", "bar", "pub", "hamburger_restaurant"],
    "metal": ["bar", "pub", "mexican_restaurant", "korean_restaurant"],
    "action": ["meal_takeaway", "fast_food_restaurant", "japanese_restaurant"],
    "shonen": ["fast_food_restaurant", "japanese_restaurant", "ramen_restaurant"],
    
    # Chill/Slice-of-life → cafes, bakeries, cozy spots
    "jazz": ["cafe", "bakery", "french_restaurant", "wine_bar"],
    "classical": ["cafe", "french_restaurant", "fine_dining_restaurant"],
    "slice of life": ["cafe", "bakery", "dessert_shop"],
    "romance": ["cafe", "italian_restaurant", "french_restaurant"],
    
    # Electronic/Sci-fi → modern, fusion, high-end
    "electronic": ["fusion_restaurant", "bar", "night_club"],
    "sci-fi": ["fusion_restaurant", "japanese_restaurant"],
    
    # Indie/Pop → casual, trendy, vegetarian
    "indie": ["vegetarian_restaurant", "vegan_restaurant", "cafe"],
    "pop": ["cafe", "pizza_restaurant", "sushi_restaurant"],
}

# Per-source weight multipliers so explicit likes (low volume but intentional)
# are not drowned out by Spotify's high-volume implicit signal.
_SPOTIFY_WEIGHT = 1.0   # Spotify profile already normalized to sum ~50
_ANIME_WEIGHT   = 2.0   # Each explicit anime like contributes 2.0 per genre
_RESTAURANT_WEIGHT = 2.0  # Restaurant type contributes 2.0 per liked restaurant
_ANILIST_WEIGHT = 2.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_spotify_genre_profile(
    user_id: str, token: str
) -> Dict[str, float]:
    """
    Fetch the user's top artists from Spotify and return a weighted genre profile.

    Imports compute_genre_profile and normalize_genres directly from
    routers.spotify — no duplication of that logic.
    """
    try:
        from routers.spotify import compute_genre_profile, normalize_genres  # type: ignore[import]
    except ImportError:
        return {}

    try:
        resp = requests.get(
            "https://api.spotify.com/v1/me/top/artists?limit=50",
            headers={"Authorization": f"Bearer {token}"},
            timeout=6,
        )
        if resp.status_code != 200:
            return {}
        artists = resp.json().get("items", [])
        # Normalise genres into broad categories (reuses existing logic)
        for artist in artists:
            artist["genres"] = normalize_genres(artist.get("genres", []))
        return compute_genre_profile(artists)
    except Exception as exc:
        print(f"[taste_profile] Spotify fetch error: {exc}")
        return {}


def _anime_genre_signal(user_id: str) -> Dict[str, float]:
    """
    Return a genre-frequency dict from the user's liked anime entries.

    Looks each liked mal_id up in the in-memory catalog held by routers.anime.
    Skips items not found in catalog (catalog may be empty in tests — mocked).
    """
    likes = get_likes(user_id, module="anime")
    if not likes:
        return {}

    try:
        from routers.anime import catalog as anime_catalog, mal_id_to_index  # type: ignore[import]
    except ImportError:
        return {}

    profile: Dict[str, float] = {}
    for like in likes:
        try:
            mal_id = int(like["item_id"])
        except (ValueError, KeyError):
            continue
        idx = mal_id_to_index.get(mal_id)
        if idx is None:
            continue
        entry = anime_catalog[idx]
        for genre in entry.get("genres", []):
            genre_key = genre.lower()
            profile[genre_key] = profile.get(genre_key, 0.0) + _ANIME_WEIGHT

    return profile


def _anilist_genre_signal(user_id: str) -> Dict[str, float]:
    """
    Return a genre-frequency dict from the user's AniList anime list.
    """
    anilist_user = get_anilist_user(user_id)
    if not anilist_user:
        return {}

    access_token = anilist_user.get("access_token")
    anilist_id = anilist_user.get("anilist_id")
    if not access_token or not anilist_id:
        return {}

    anime_list = fetch_user_anime_list(access_token, anilist_id)
    if not anime_list:
        return {}

    try:
        from routers.anime import catalog as anime_catalog, mal_id_to_index  # type: ignore[import]
    except ImportError:
        return {}

    profile: Dict[str, float] = {}
    for entry in anime_list:
        status = entry.get("status")
        if status not in {"CURRENT", "COMPLETED", "REPEATING"}:
            continue

        mal_id = entry.get("mal_id")
        score = entry.get("score", 0.0)

        idx = mal_id_to_index.get(mal_id)
        if idx is None:
            continue

        if score > 0:
            weight = (score / 10.0) * _ANILIST_WEIGHT
        elif status == "COMPLETED" and score == 0:
            weight = 0.5 * _ANILIST_WEIGHT
        else:
            continue

        anime_entry = anime_catalog[idx]
        for genre in anime_entry.get("genres", []):
            genre_key = genre.lower()
            profile[genre_key] = profile.get(genre_key, 0.0) + weight

    return profile


CUISINE_ALLOWLIST = {
    "italian_restaurant", "japanese_restaurant", "mexican_restaurant", 
    "korean_restaurant", "french_restaurant", "fast_food_restaurant", 
    "ramen_restaurant", "vegetarian_restaurant", "vegan_restaurant", 
    "sushi_restaurant", "pizza_restaurant", "hamburger_restaurant",
    "seafood_restaurant", "mediterranean_restaurant", "brunch_restaurant",
    "dessert_restaurant", "fine_dining_restaurant", "fusion_restaurant",
    "cafe", "bar", "pub", "wine_bar", "night_club", "bakery", "dessert_shop",
    "family_restaurant", "meal_takeaway", "coffee_shop", "ice_cream_shop"
}

def _restaurant_cuisine_signal(user_id: str) -> Dict[str, Any]:
    """
    Return a cuisine-frequency dict and avg rating/price from the user's liked restaurants.
    """
    likes = get_likes(user_id, module="restaurants")
    if not likes:
        return {"cuisines": {}, "avg_rating": None, "avg_price": None}

    try:
        from services.google_places_client import get_restaurant_details  # type: ignore[import]
    except ImportError:
        return {"cuisines": {}, "avg_rating": None, "avg_price": None}

    cuisines: Dict[str, float] = {}
    total_rating = 0.0
    rating_count = 0
    total_price = 0.0
    price_count = 0

    for like in likes:
        place_id = like.get("item_id", "")
        if not place_id:
            continue
        
        # In a real system, you might cache these directly in the database or use the TTL cache
        # If the TTL cache misses, this makes network requests! It's okay for prototype/mocked tests.
        entry = get_restaurant_details(place_id)
        if not entry:
            continue
            
        for r_type in entry.get("types", []):
            cat = r_type.lower()
            if cat in CUISINE_ALLOWLIST:
                cuisines[cat] = cuisines.get(cat, 0.0) + _RESTAURANT_WEIGHT

        r = entry.get("rating")
        if r is not None:
            total_rating += r
            rating_count += 1
            
        p = entry.get("price_level")
        if p is not None:
            total_price += p
            price_count += 1

    return {
        "cuisines": cuisines,
        "avg_rating": total_rating / rating_count if rating_count > 0 else None,
        "avg_price": total_price / price_count if price_count > 0 else None,
    }


def _merge_profiles(*profiles: Dict[str, float]) -> Dict[str, float]:
    """Sum multiple genre/keyword dicts into one merged profile."""
    merged: Dict[str, float] = {}
    for prof in profiles:
        for key, val in prof.items():
            merged[key] = merged.get(key, 0.0) + val
    return merged


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_taste_profile(
    user_id: str,
    spotify_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a combined cross-module taste profile for the given user.

    Parameters
    ----------
    user_id:
        The authenticated user's ID (from the session cookie).
    spotify_token:
        A valid Spotify access token for this user, used to fetch top artists.
        If None (or if the fetch fails), the Spotify signal is silently skipped.

    Returns
    -------
    dict with keys:
      "profile"        — merged {genre/keyword: float} dict, sorted by weight desc
      "breakdown"      — per-source sub-profiles for debugging
      "crosswalk_anime" — anime genre keywords derived from Spotify genres via
                          GENRE_CROSSWALK (used by the ?personalize=true boost)
    """
    # --- Gather per-source signals ---
    spotify_profile: Dict[str, float] = {}
    if spotify_token:
        raw = _fetch_spotify_genre_profile(user_id, spotify_token)
        spotify_profile = {k: v * _SPOTIFY_WEIGHT for k, v in raw.items()}

    anime_profile = _anime_genre_signal(user_id)
    anilist_profile = _anilist_genre_signal(user_id)
    
    restaurant_data = _restaurant_cuisine_signal(user_id)
    restaurant_profile = restaurant_data.get("cuisines", {})
    avg_price = restaurant_data.get("avg_price")
    avg_rating = restaurant_data.get("avg_rating")

    merged = _merge_profiles(spotify_profile, anime_profile, anilist_profile, restaurant_profile)

    # --- Build anime crosswalk from Spotify genres ---
    crosswalk_anime: Dict[str, float] = {}
    for sp_genre, weight in spotify_profile.items():
        for anime_genre in GENRE_CROSSWALK.get(sp_genre, []):
            crosswalk_anime[anime_genre] = (
                crosswalk_anime.get(anime_genre, 0.0) + weight
            )
            
    # --- Build restaurants crosswalk from Spotify + Anime genres ---
    crosswalk_restaurants: Dict[str, float] = {}
    # Incorporate spotify and anime into the cuisine crosswalk
    combined_signal = _merge_profiles(spotify_profile, anime_profile, anilist_profile)
    for genre, weight in combined_signal.items():
        for cuisine in CUISINE_CROSSWALK.get(genre, []):
            crosswalk_restaurants[cuisine] = (
                crosswalk_restaurants.get(cuisine, 0.0) + weight
            )

    # Fetch AniList watched list with titles
    anilist_watched = []
    try:
        anilist_user = get_anilist_user(user_id)
        if anilist_user:
            access_token = anilist_user.get("access_token")
            anilist_id = anilist_user.get("anilist_id")
            if access_token and anilist_id:
                raw_list = fetch_user_anime_list(access_token, anilist_id)
                for entry in raw_list:
                    if entry.get("status") in {"CURRENT", "COMPLETED", "REPEATING"}:
                        anilist_watched.append({
                            "mal_id": entry.get("mal_id"),
                            "title": entry.get("title"),
                            "score": entry.get("score"),
                            "status": entry.get("status")
                        })
    except Exception as exc:
        print(f"[taste_profile] failed to fetch anilist_watched: {exc}")

    # Sort merged profile descending by weight
    sorted_profile = dict(
        sorted(merged.items(), key=lambda x: x[1], reverse=True)
    )

    return {
        "profile": sorted_profile,
        "breakdown": {
            "spotify": dict(sorted(spotify_profile.items(), key=lambda x: x[1], reverse=True)),
            "anime": anime_profile,
            "anilist": anilist_profile,
            "restaurants": restaurant_profile,
        },
        "restaurant_features": {
            "avg_rating": avg_rating,
            "avg_price_level": avg_price
        },
        "anilist_watched": anilist_watched,
        "crosswalk_anime": crosswalk_anime,
        "crosswalk_restaurants": crosswalk_restaurants,
    }



def get_anime_boost_map(user_id: str, spotify_token: Optional[str] = None) -> Dict[str, float]:
    """
    Return a {anime_genre_lower: boost_weight} dict for use in
    routers/anime.py's ?personalize=true re-ranking.

    Combines crosswalk-derived Spotify genres with directly liked anime genres.
    """
    profile_data = compute_taste_profile(user_id, spotify_token=spotify_token)
    boost_map = dict(profile_data["crosswalk_anime"])

    # Also directly boost genres of liked anime (already in profile)
    for genre, weight in profile_data["breakdown"]["anime"].items():
        boost_map[genre] = boost_map.get(genre, 0.0) + weight

    # Also directly boost genres of AniList anime
    for genre, weight in profile_data["breakdown"].get("anilist", {}).items():
        boost_map[genre] = boost_map.get(genre, 0.0) + weight

    return boost_map


def get_restaurant_boost_map(user_id: str, spotify_token: Optional[str] = None) -> Dict[str, float]:
    """
    Return a {cuisine_lower: boost_weight} dict for use in
    routers/restaurants.py's ?personalize=true re-ranking.
    """
    profile_data = compute_taste_profile(user_id, spotify_token=spotify_token)
    boost_map = dict(profile_data.get("crosswalk_restaurants", {}))

    # Also directly boost cuisines of liked restaurants
    for genre, weight in profile_data.get("breakdown", {}).get("restaurants", {}).items():
        boost_map[genre] = boost_map.get(genre, 0.0) + weight

    return boost_map
