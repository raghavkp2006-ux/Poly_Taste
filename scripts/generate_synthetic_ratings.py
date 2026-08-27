"""
scripts/generate_synthetic_ratings.py — Generate genre-biased synthetic personal ratings for movies.

=============================================================================
NOTICE: This script generates SYNTHETIC placeholder ratings biased by stated
genre/keyword preferences, NOT real user ratings.
Flagged for future replacement with genuine personal ratings data (e.g. IMDb import).
=============================================================================

Rating Computation Logic:
1. Skips movies with vote_average == 0.0 or None (unreleased/unvoted movies, leaves personal_rating=None).
2. Base score = movie.vote_average (0-10 scale from TMDB).
3. Genre Boost: +1.0 if genre list contains ANY of:
   Action, Science Fiction, Thriller, Drama, Comedy, Romance, Fantasy, Adventure.
   (Applied at most once per movie).
4. Keyword Boost: +1.5 if title contains 'James Bond' or '007' (case-insensitive).
5. Gaussian noise: random.gauss(mu=0.0, sigma=0.6) with fixed seed=42 for reproducibility.
6. Clamped to [1.0, 10.0] and rounded to 1 decimal place.

Usage:
    python scripts/generate_synthetic_ratings.py
"""

import json
import os
import random
import sys
from typing import List, Set

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Fixed random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

TARGET_GENRES: Set[str] = {
    "Action",
    "Science Fiction",
    "Thriller",
    "Drama",
    "Comedy",
    "Romance",
    "Fantasy",
    "Adventure",
}

GENRE_BOOST = 1.0
KEYWORD_BOOST = 1.5
NOISE_MU = 0.0
NOISE_SIGMA = 0.6
MIN_RATING = 1.0
MAX_RATING = 10.0


def compute_synthetic_rating(title: str, genres: List[str], vote_avg: float) -> tuple[float, bool, bool]:
    """Compute synthetic personal rating for a movie.

    Returns:
        (personal_rating, has_genre_boost, has_keyword_boost)
    """
    has_genre_boost = any(g in TARGET_GENRES for g in genres)
    has_keyword_boost = ("james bond" in title.lower()) or ("007" in title.lower())

    rating = vote_avg
    if has_genre_boost:
        rating += GENRE_BOOST
    if has_keyword_boost:
        rating += KEYWORD_BOOST

    noise = random.gauss(NOISE_MU, NOISE_SIGMA)
    rating += noise

    clamped = max(MIN_RATING, min(MAX_RATING, rating))
    final_rating = round(clamped, 1)

    return final_rating, has_genre_boost, has_keyword_boost


def main():
    print("=" * 65)
    print("Generate Synthetic Personal Movie Ratings")
    print(f"Random Seed: {RANDOM_SEED} (Python random.gauss)")
    print("=" * 65)

    os.environ.setdefault("USE_LOCAL_DB", "true")
    from database import SessionLocal, Movie

    db = SessionLocal()
    try:
        movies = db.query(Movie).all()
        total = len(movies)
        print(f"\nTotal movies in DB: {total}")

        rated_count = 0
        skipped_count = 0
        genre_boosted_count = 0
        keyword_boosted_count = 0

        genre_matched_ratings: List[float] = []
        non_matched_ratings: List[float] = []
        bond_movies: List[dict] = []

        for movie in movies:
            vote_avg = movie.vote_average

            # Zero-vote / unvoted movie check: skip if 0.0 or None
            if vote_avg is None or vote_avg == 0.0 or vote_avg == 0:
                movie.personal_rating = None
                skipped_count += 1
                continue

            genres: List[str] = json.loads(movie.genres_json) if movie.genres_json else []
            rating, has_genre_boost, has_keyword_boost = compute_synthetic_rating(
                title=movie.title,
                genres=genres,
                vote_avg=vote_avg,
            )

            movie.personal_rating = rating
            rated_count += 1

            if has_genre_boost:
                genre_boosted_count += 1
                genre_matched_ratings.append(rating)
            else:
                non_matched_ratings.append(rating)

            if has_keyword_boost:
                keyword_boosted_count += 1
                bond_movies.append({
                    "tmdb_id": movie.tmdb_id,
                    "title": movie.title,
                    "vote_average": vote_avg,
                    "personal_rating": rating,
                })

        db.commit()

        print("\n--- Execution Summary ---")
        print(f"Total movies processed: {total}")
        print(f"Movies rated: {rated_count}")
        print(f"Movies skipped (zero-vote): {skipped_count}")
        print(f"Genre boosted (+{GENRE_BOOST}): {genre_boosted_count}")
        print(f"Keyword boosted (+{KEYWORD_BOOST}): {keyword_boosted_count}")

        # Verification metrics
        avg_genre = sum(genre_matched_ratings) / len(genre_matched_ratings) if genre_matched_ratings else 0.0
        avg_non_genre = sum(non_matched_ratings) / len(non_matched_ratings) if non_matched_ratings else 0.0

        print("\n--- Rating Comparisons ---")
        print(f"Average rating for genre-matched movies ({len(genre_matched_ratings)}): {avg_genre:.2f}")
        print(f"Average rating for non-matched movies ({len(non_matched_ratings)}): {avg_non_genre:.2f}")
        print(f"Net genre boost in data: +{avg_genre - avg_non_genre:.2f}")

        print("\n--- James Bond / 007 Matches ---")
        if bond_movies:
            for b in bond_movies:
                print(f"  tmdb_id={b['tmdb_id']} | title={b['title']} | TMDB={b['vote_average']} | Personal={b['personal_rating']}")
        else:
            print("  None found in the current 255 movie catalog.")

        print("\n--- 5 Sample Rows ---")
        # Sample 5 random rows from rated movies
        sample_movies = random.sample([m for m in movies if m.personal_rating is not None], 5)
        for s in sample_movies:
            g = json.loads(s.genres_json) if s.genres_json else []
            print(f"  tmdb_id={s.tmdb_id} | title={s.title}")
            print(f"    genres={g}")
            print(f"    TMDB vote_average={s.vote_average} -> synthetic personal_rating={s.personal_rating}")

    except Exception as e:
        db.rollback()
        print(f"\nFATAL ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
