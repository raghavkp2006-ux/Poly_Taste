"""
scripts/backfill_vote_average.py — Backfill TMDB vote_average for existing Movie records.

Loops over existing Movie rows in the database, queries TMDB /movie/{tmdb_id},
and updates ONLY the vote_average column. Preserves all other columns and row count.

Usage
-----
    python scripts/backfill_vote_average.py

Requires TMDB_API_KEY in the project .env file.
"""

import os
import ssl
import sys
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
REQUEST_DELAY = 0.3  # seconds between requests to respect rate limits


# ---------------------------------------------------------------------------
# TLS 1.2 adapter — works around UNEXPECTED_EOF_WHILE_READING on Windows
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


def _tmdb_get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{TMDB_BASE_URL}{endpoint}"
    all_params = {"api_key": TMDB_API_KEY}
    if params:
        all_params.update(params)

    resp = _session.get(url, params=all_params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_vote_average(tmdb_id: int) -> Optional[float]:
    for attempt in range(3):
        try:
            data = _tmdb_get(f"/movie/{tmdb_id}", {"language": "en-US"})
            vote = data.get("vote_average")
            return float(vote) if vote is not None else None
        except requests.RequestException as e:
            if attempt == 2:
                print(f"    Detail fetch failed for tmdb_id={tmdb_id}: {e}")
                return None
            time.sleep(1.0)
    return None


def main():
    if not TMDB_API_KEY:
        print("ERROR: TMDB_API_KEY not found in environment.")
        sys.exit(1)

    print("=" * 60)
    print("TMDB Movie vote_average Backfill")
    print("=" * 60)

    os.environ.setdefault("USE_LOCAL_DB", "true")
    from database import SessionLocal, Movie

    db = SessionLocal()
    try:
        movies = db.query(Movie).all()
        to_fetch = [m for m in movies if m.vote_average is None]
        total = len(to_fetch)
        print(f"\nTotal movies in DB: {len(movies)}")
        print(f"Movies needing vote_average backfill: {total}")

        updated = 0
        errors = 0

        for i, movie in enumerate(to_fetch):
            time.sleep(REQUEST_DELAY)
            vote_avg = fetch_vote_average(movie.tmdb_id)

            if vote_avg is not None:
                movie.vote_average = vote_avg
                updated += 1
            else:
                errors += 1

            if (i + 1) % 50 == 0 or (i + 1) == total:
                db.commit()
                print(f"  [{i+1}/{total}] Progress... updated={updated}, errors={errors}")

        db.commit()
        print(f"\nBackfill pass complete! Newly updated: {updated}, Errors: {errors}")

        # Verification
        final_count = db.query(Movie).count()
        with_vote = db.query(Movie).filter(Movie.vote_average.isnot(None)).count()
        print(f"Total movies in DB: {final_count}")
        print(f"Movies with vote_average populated: {with_vote}")

        print(f"\n{'=' * 60}")
        print("5 Sample rows:")
        print("=" * 60)
        samples = db.query(Movie).limit(5).all()
        for s in samples:
            print(f"  tmdb_id={s.tmdb_id} | title={s.title} | vote_average={s.vote_average}")

    except Exception as e:
        db.rollback()
        print(f"\nFATAL ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
