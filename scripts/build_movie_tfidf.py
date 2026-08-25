"""
scripts/build_movie_tfidf.py — Precompute TF-IDF matrix and vectorizer for movies.

Reads all 255 movies from the database, combines overview + genres text,
fits a TfidfVectorizer, computes the TF-IDF matrix, and saves artifacts to data/processed/.

Usage:
    python scripts/build_movie_tfidf.py
"""

import json
import os
import pickle
import sys
from typing import Any, Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))


def main():
    print("=" * 60)
    print("Build Movie TF-IDF Precomputed Matrix")
    print("=" * 60)

    os.environ.setdefault("USE_LOCAL_DB", "true")
    from database import SessionLocal, Movie

    db = SessionLocal()
    try:
        movies = db.query(Movie).order_by(Movie.id.asc()).all()
        total = len(movies)
        print(f"\nLoaded {total} movies from database.")

        if total == 0:
            print("ERROR: No movies found in database. Run fetch_movies.py first.")
            sys.exit(1)

        movie_ids: List[str] = []
        tmdb_ids: List[int] = []
        combined_texts: List[str] = []
        movie_metadata: Dict[str, Dict[str, Any]] = {}

        for movie in movies:
            mid_str = str(movie.tmdb_id)
            movie_ids.append(mid_str)
            tmdb_ids.append(movie.tmdb_id)

            genres = json.loads(movie.genres_json) if movie.genres_json else []
            genres_text = " ".join(genres)
            overview_text = (movie.overview or "").strip()

            combined = f"{overview_text} {genres_text}".strip()
            combined_texts.append(combined)

            movie_metadata[mid_str] = {
                "id": movie.id,
                "tmdb_id": movie.tmdb_id,
                "imdb_id": movie.imdb_id,
                "title": movie.title,
                "overview": movie.overview,
                "genres": genres,
                "release_year": movie.release_year,
                "poster_url": movie.poster_url,
                "vote_average": movie.vote_average,
                "personal_rating": movie.personal_rating,
            }

        # Fit TfidfVectorizer on all 255 combined texts
        print("\nFitting TfidfVectorizer...")
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            max_features=5000,
        )
        tfidf_sparse = vectorizer.fit_transform(combined_texts)
        tfidf_matrix = tfidf_sparse.toarray().astype(np.float32)

        vocab_size = len(vectorizer.vocabulary_)
        print(f"TF-IDF Matrix shape: {tfidf_matrix.shape} (rows x features)")
        print(f"Vocabulary size: {vocab_size} tokens/ngrams")

        # Save artifacts to data/processed/
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
        os.makedirs(out_dir, exist_ok=True)

        vec_path = os.path.join(out_dir, "movie_tfidf_vectorizer.pkl")
        mat_path = os.path.join(out_dir, "movie_tfidf_matrix.pkl")

        with open(vec_path, "wb") as f:
            pickle.dump(vectorizer, f)

        matrix_payload = {
            "matrix": tfidf_matrix,
            "ids": movie_ids,
            "metadata": movie_metadata,
        }
        with open(mat_path, "wb") as f:
            pickle.dump(matrix_payload, f)

        vec_size = os.path.getsize(vec_path)
        mat_size = os.path.getsize(mat_path)

        print("\n--- Artifacts Written ---")
        print(f"1. Vectorizer: {vec_path} ({vec_size:,} bytes)")
        print(f"2. Matrix & IDs: {mat_path} ({mat_size:,} bytes)")
        print("\nMovie TF-IDF precomputation completed successfully!")

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
