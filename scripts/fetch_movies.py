"""
scripts/fetch_movies.py — TMDB movie catalog fetch script.

Fetches popular and top-rated movies from the TMDB API, resolves genre IDs
to names, retrieves imdb_id from the detail endpoint, and inserts everything
into the ``movies`` table via the Movie ORM model.

Usage
-----
    python scripts/fetch_movies.py

Requires TMDB_API_KEY in the project .env file.
"""

import json
import os
import ssl
import sys
import time
from typing import Any, Dict, List, Set

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# TMDB free tier: ~40 requests per 10 seconds
REQUEST_DELAY = 0.3  # seconds between requests to stay well under limit


# ---------------------------------------------------------------------------
# TLS 1.2 adapter — works around UNEXPECTED_EOF_WHILE_READING on some
# Windows machines where TLS 1.3 handshake fails with TMDB's CDN.
# ---------------------------------------------------------------------------
class _TLS12Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

_session = requests.Session()
_session.mount("https://", _TLS12Adapter())


def _tmdb_get(endpoint: str, params: dict = None) -> dict:
    """Make an authenticated GET request to the TMDB v3 API."""
    url = f"{TMDB_BASE_URL}{endpoint}"
    all_params = {"api_key": TMDB_API_KEY}
    if params:
        all_params.update(params)

    resp = _session.get(url, params=all_params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_genre_map() -> Dict[int, str]:
    """Fetch the TMDB movie genre list and return {id: name} mapping."""
    data = _tmdb_get("/genre/movie/list", {"language": "en-US"})
    genre_map = {g["id"]: g["name"] for g in data.get("genres", [])}
    print(f"  Loaded {len(genre_map)} genre mappings from TMDB.")
    return genre_map


def fetch_movie_lists() -> List[Dict[str, Any]]:
    """Fetch popular + top-rated movie lists, returning deduplicated raw entries."""
    seen_ids: Set[int] = set()
    movies: List[Dict[str, Any]] = []

    endpoints = [
        ("/movie/popular", 7),     # 7 pages x 20 = 140 movies
        ("/movie/top_rated", 7),   # 7 pages x 20 = 140 movies
    ]

    for endpoint, num_pages in endpoints:
        label = endpoint.split("/")[-1]
        print(f"\n  Fetching {label} (up to {num_pages} pages)...")
        for page in range(1, num_pages + 1):
            try:
                data = _tmdb_get(endpoint, {"language": "en-US", "page": page})
                results = data.get("results", [])
                if not results:
                    print(f"    Page {page}: empty, stopping.")
                    break

                new_count = 0
                for movie in results:
                    tmdb_id = movie.get("id")
                    if tmdb_id and tmdb_id not in seen_ids:
                        seen_ids.add(tmdb_id)
                        movies.append(movie)
                        new_count += 1

                print(f"    Page {page}: {len(results)} results, {new_count} new (total unique: {len(movies)})")
                time.sleep(REQUEST_DELAY)

            except requests.RequestException as e:
                print(f"    Page {page}: ERROR - {e}")
                break

    print(f"\n  Total unique movies from lists: {len(movies)}")
    return movies


def fetch_movie_detail(tmdb_id: int) -> dict:
    """Fetch the full movie detail to get imdb_id and other metadata."""
    try:
        data = _tmdb_get(f"/movie/{tmdb_id}", {"language": "en-US"})
        return data
    except requests.RequestException as e:
        print(f"    Detail fetch failed for tmdb_id={tmdb_id}: {e}")
        return None


def main():
    if not TMDB_API_KEY:
        print("ERROR: TMDB_API_KEY not found in environment.")
        print("Add TMDB_API_KEY=your_key_here to your .env file.")
        print("Get a free API key at https://www.themoviedb.org/settings/api")
        sys.exit(1)

    print("=" * 60)
    print("TMDB Movie Catalog Fetch")
    print("=" * 60)

    # Step 1: Fetch genre mapping
    print("\n[1/3] Fetching genre mappings...")
    genre_map = fetch_genre_map()

    # Step 2: Fetch popular + top-rated lists
    print("\n[2/3] Fetching movie lists (popular + top_rated)...")
    raw_movies = fetch_movie_lists()

    # Step 3: Fetch detail for each movie (to get imdb_id) and insert into DB
    print(f"\n[3/3] Fetching details and inserting {len(raw_movies)} movies into DB...")

    # Import DB dependencies here so the script fails fast on missing API key
    os.environ.setdefault("USE_LOCAL_DB", "true")
    from database import SessionLocal, Movie

    db = SessionLocal()
    inserted = 0
    skipped = 0
    errors = 0

    try:
        for i, raw in enumerate(raw_movies):
            tmdb_id = raw["id"]
            title = raw.get("title", "Unknown")

            # Check for existing record
            existing = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
            if existing:
                skipped += 1
                if (i + 1) % 50 == 0:
                    print(f"    [{i+1}/{len(raw_movies)}] Progress... (inserted={inserted}, skipped={skipped})")
                continue

            # Fetch detail for imdb_id
            time.sleep(REQUEST_DELAY)
            detail = fetch_movie_detail(tmdb_id)

            imdb_id = None
            if detail:
                imdb_id = detail.get("imdb_id")  # e.g. "tt0111161"

            # Resolve genre IDs to names
            genre_ids = raw.get("genre_ids", [])
            genre_names = [genre_map[gid] for gid in genre_ids if gid in genre_map]

            # Extract release year from release_date ("2024-01-15" -> 2024)
            release_date = raw.get("release_date", "")
            release_year = None
            if release_date and len(release_date) >= 4:
                try:
                    release_year = int(release_date[:4])
                except ValueError:
                    pass

            # Construct full poster URL
            poster_path = raw.get("poster_path")
            poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None

            movie = Movie(
                tmdb_id=tmdb_id,
                imdb_id=imdb_id,
                title=title,
                overview=raw.get("overview", ""),
                genres_json=json.dumps(genre_names) if genre_names else None,
                release_year=release_year,
                poster_url=poster_url,
                personal_rating=None,  # Will be populated in Part 3 (IMDb CSV import)
            )
            db.add(movie)
            inserted += 1

            if (i + 1) % 50 == 0:
                db.commit()
                print(f"    [{i+1}/{len(raw_movies)}] Progress... (inserted={inserted}, skipped={skipped})")

        db.commit()
        print(f"\n  Done! Inserted: {inserted}, Skipped (already existed): {skipped}, Errors: {errors}")

    except Exception as e:
        db.rollback()
        print(f"\n  FATAL ERROR: {e}")
        raise
    finally:
        db.close()

    # Print sample rows
    print(f"\n{'=' * 60}")
    print("Sample rows from DB:")
    print("=" * 60)
    db = SessionLocal()
    try:
        samples = db.query(Movie).limit(3).all()
        for s in samples:
            d = s.to_dict()
            print(f"\n  tmdb_id={d['tmdb_id']} | imdb_id={d['imdb_id']} | title={d['title']}")
            print(f"    genres={d['genres']} | year={d['release_year']}")
            print(f"    poster={d['poster_url']}")
            print(f"    overview={d['overview'][:100]}...")

        total = db.query(Movie).count()
        with_imdb = db.query(Movie).filter(Movie.imdb_id.isnot(None)).count()
        print(f"\n  Total movies in DB: {total}")
        print(f"  Movies with imdb_id: {with_imdb}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
