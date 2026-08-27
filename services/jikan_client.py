import requests
import time
import json
from typing import List, Dict, Any
import os

# In-memory cache so we don't re-fetch the same genre relationship URL
# across entries in a single catalog-build run.
_genre_cache: Dict[str, List[str]] = {}


def _fetch_kitsu_genres(related_url: str) -> List[str]:
    """
    Fetch genre names from a Kitsu relationship URL, e.g.:
        https://kitsu.io/api/edge/anime/1/genres

    Returns a list of genre name strings, or [] on any error.
    Results are memoised in ``_genre_cache`` to avoid duplicate requests.
    """
    if related_url in _genre_cache:
        return _genre_cache[related_url]

    try:
        resp = requests.get(related_url, timeout=5)
        if resp.status_code == 200:
            names = [
                item["attributes"]["name"]
                for item in resp.json().get("data", [])
                if item.get("attributes", {}).get("name")
            ]
            _genre_cache[related_url] = names
            return names
        else:
            print(f"    [genres] HTTP {resp.status_code} for {related_url}")
    except Exception as exc:
        print(f"    [genres] Error fetching {related_url}: {exc}")

    _genre_cache[related_url] = []
    return []


def fetch_top_anime() -> List[Dict[str, Any]]:
    """
    Fetches the top anime from the Kitsu open API (fallback since Jikan is down).

    Genres are now populated via Kitsu's relationships endpoint so that the
    TF-IDF vectoriser in routers/anime.py has real signal to work with.
    Runs locally as a one-off script, or scheduled.
    """
    print("Fetching top anime from Kitsu API...")
    url = "https://kitsu.io/api/edge/anime"
    catalog: List[Dict[str, Any]] = []

    # Fetch a few pages to get a good dataset
    for page in range(0, 5):
        try:
            params = {
                "page[limit]": 20,
                "page[offset]": page * 20,
                "sort": "-averageRating",  # Top rated
                # Ask Kitsu to include genre relationships in the same response
                "include": "genres",
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch offset {page * 20}: {response.status_code}")
                break

            body = response.json()
            items = body.get("data", [])

            # Build a lookup from included genre records
            included_genres: Dict[str, str] = {}  # id -> name
            for included in body.get("included", []):
                if included.get("type") == "genres":
                    gid = included.get("id")
                    gname = included.get("attributes", {}).get("name")
                    if gid and gname:
                        included_genres[gid] = gname

            for item in items:
                attrs = item.get("attributes", {})
                
                # Filter out adult-rated anime
                if attrs.get("ageRating") == "R18":
                    continue

                relationships = item.get("relationships", {})

                # --- Resolve genres ---
                genres: List[str] = []

                # Strategy 1: inline included data (fast, no extra request)
                genre_rel = relationships.get("genres", {})
                genre_data = genre_rel.get("data")
                if isinstance(genre_data, list):
                    for gref in genre_data:
                        gname = included_genres.get(gref.get("id", ""))
                        if gname:
                            genres.append(gname)

                # Strategy 2: follow the relationship link if inline data missing
                if not genres:
                    genre_link = genre_rel.get("links", {}).get("related")
                    if genre_link:
                        genres = _fetch_kitsu_genres(genre_link)
                        # Small delay to be polite to the Kitsu API
                        time.sleep(0.05)

                catalog.append({
                    "mal_id": int(item.get("id")),  # Using Kitsu ID as stand-in
                    "title": attrs.get("canonicalTitle"),
                    "synopsis": attrs.get("description", ""),
                    "genres": genres,
                    "score": float(attrs.get("averageRating") or 0) / 10.0,
                    "image_url": attrs.get("posterImage", {}).get("original"),
                })

        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

        time.sleep(0.1)

    print(f"Fetched {len(catalog)} anime.")
    genre_counts = sum(1 for a in catalog if a["genres"])
    print(f"  {genre_counts}/{len(catalog)} entries have genre data.")
    return catalog


def upload_catalog_to_s3(catalog: list) -> None:
    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/anime_catalog.json", "w") as f:
        json.dump(catalog, f)


def get_catalog_from_s3() -> List[Dict[str, Any]]:
    """Loads catalog for inference (local fallback when S3_BUCKET_NAME not set)."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "raw",
        "anime_catalog.json",
    )
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


if __name__ == "__main__":
    catalog = fetch_top_anime()
    upload_catalog_to_s3(catalog)
