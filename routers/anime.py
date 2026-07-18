import os
import torch
import torch.nn as nn
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer

from services.jikan_client import get_catalog_from_s3
from models.anime_dnn import AnimeAutoEncoder

router = APIRouter(prefix="/anime", tags=["anime"])

# --- Setup State at Cold Start ---
catalog = get_catalog_from_s3()
mal_id_to_index = {anime['mal_id']: i for i, anime in enumerate(catalog)}

# Fit TF-IDF on the catalog
tf_idf_matrix = None
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

if catalog:
    # Combine synopsis and genres for text representation
    texts = [f"{anime.get('synopsis', '')} {' '.join(anime.get('genres', []))}" for anime in catalog]
    tf_idf_matrix = vectorizer.fit_transform(texts).toarray() # Shape: (N, 1000)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
anime_model = AnimeAutoEncoder(input_dim=1000, latent_dim=32).to(device)

model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'models', 'anime_model.pth')
if os.path.exists(model_path):
    anime_model.load_state_dict(torch.load(model_path, map_location=device))
anime_model.eval()

# Precompute latent representations for the catalog if we have data
latent_catalog = None
if tf_idf_matrix is not None:
    with torch.no_grad():
        tf_idf_tensor = torch.tensor(tf_idf_matrix, dtype=torch.float32).to(device)
        latent_catalog = anime_model.encode(tf_idf_tensor)

@router.get("/search")
def search_anime(q: str):
    """Substring search on catalog titles."""
    results = [anime for anime in catalog if q.lower() in anime['title'].lower()]
    return {"results": results[:10]}

@router.get("/{mal_id}")
def get_anime(mal_id: int):
    if mal_id not in mal_id_to_index:
        raise HTTPException(status_code=404, detail="Anime not found in catalog")
    return catalog[mal_id_to_index[mal_id]]

@router.get("/{mal_id}/recommend")
def recommend_anime(mal_id: int, n: int = 5):
    """
    Computes cosine similarity in the latent space of the AutoEncoder.
    """
    if mal_id not in mal_id_to_index:
        raise HTTPException(status_code=404, detail="Anime not found in catalog")
        
    if latent_catalog is None:
        raise HTTPException(status_code=500, detail="Model or catalog not properly loaded")
        
    seed_idx = mal_id_to_index[mal_id]
    seed_latent = latent_catalog[seed_idx].unsqueeze(0) # (1, 32)
    
    # Compute cosine similarity between seed and all items
    cos = nn.CosineSimilarity(dim=1, eps=1e-6)
    similarities = cos(seed_latent, latent_catalog) # (N,)
    
    # Get top N indices (excluding itself)
    # PyTorch topk
    scores, indices = torch.topk(similarities, n + 1)
    
    recommendations = []
    for score, idx in zip(scores, indices):
        idx = idx.item()
        if idx == seed_idx:
            continue
        rec_anime = catalog[idx].copy()
        rec_anime["similarity_score"] = round(score.item(), 4)
        recommendations.append(rec_anime)
        
        if len(recommendations) == n:
            break
            
    return {"recommendations": recommendations}
