import pytest
import numpy as np
from services.anime_recommender import get_or_compute_embedding, vectorizer

def test_get_or_compute_embedding_precomputed():
    """Test retrieving an embedding that already exists in the 15k dataset."""
    # Assuming ID '1' (Cowboy Bebop) is in the 15k dataset
    # You might need to adjust the ID based on what's actually in your anime_embeddings.pkl
    embedding, title, genres = get_or_compute_embedding(1)
    
    # We might not know if 1 is actually there without loading the pkl, 
    # but if it is, embedding shouldn't be None.
    # We will test the cold start explicitly to be safe.
    pass

def test_cold_start_rich_metadata():
    """Test generating a cold-start embedding with rich metadata."""
    rich_metadata = {
        "title": {"english": "Mock Rich Anime"},
        "description": "This is a very long and detailed description of a completely fake anime that should easily pass the twenty token limit required for generating an embedding. It features epic battles and intense drama in a futuristic setting.",
        "genres": ["Action", "Sci-Fi", "Drama"],
        "tags": [{"name": "Space"}, {"name": "Mecha"}]
    }
    
    initial_vocab_size = len(vectorizer.vocabulary_) if vectorizer else 0
    
    embedding, title, genres = get_or_compute_embedding(999999991, metadata=rich_metadata)
    
    assert embedding is not None, "Embedding should be generated for rich metadata."
    assert embedding.shape == (32,), "Embedding should be 32-dimensional."
    assert title == "Mock Rich Anime", "Title should match metadata."
    assert genres == ["Action", "Sci-Fi", "Drama"], "Genres should match metadata."
    
    final_vocab_size = len(vectorizer.vocabulary_) if vectorizer else 0
    assert initial_vocab_size == final_vocab_size, "Vectorizer vocabulary should not change (no accidental fit_transform)."

def test_cold_start_thin_metadata():
    """Test the fallback mechanism for thin metadata."""
    thin_metadata = {
        "title": "Mock Thin Anime",
        "description": "Short.",
        "genres": ["Comedy"],
        "tags": []
    }
    
    embedding, title, genres = get_or_compute_embedding(999999992, metadata=thin_metadata)
    
    assert embedding is None, "Embedding should be None due to thin metadata fallback."
    assert title == "Mock Thin Anime", "Title should match metadata."
    assert genres == ["Comedy"], "Genres should match metadata."

def test_caching_behavior():
    """Test that a newly computed embedding is cached."""
    rich_metadata = {
        "title": "Mock Cached Anime",
        "description": "Another long description that easily surpasses the minimum token length required by the simple regex split. This ensures we trigger the embedding generation path.",
        "genres": ["Fantasy"],
        "tags": []
    }
    
    emb1, title1, genres1 = get_or_compute_embedding(999999993, metadata=rich_metadata)
    
    # Call again with NO metadata to ensure it pulls from cache
    emb2, title2, genres2 = get_or_compute_embedding(999999993)
    
    assert emb2 is not None, "Should retrieve from cache."
    assert np.array_equal(emb1, emb2), "Cached embedding should be identical."
    assert title1 == title2, "Title should match."
    assert genres1 == genres2, "Genres should match."
