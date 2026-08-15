import os
import pickle
import torch
import torch.nn as nn
from typing import Optional, Dict, Any, Tuple
import numpy as np

# Adjust imports based on your project structure
from models.anime_dnn import AnimeAutoEncoder
from services.anilist_client import fetch_anime_metadata

# ---------------------------------------------------------------------------
# Global State & Model Loading
# ---------------------------------------------------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def _download_from_s3_if_needed(key: str, local_path: str) -> None:
    """Download a file from S3 if S3_BUCKET_NAME is set and local file does not exist."""
    if not S3_BUCKET_NAME or os.path.exists(local_path):
        return
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        import boto3
        s3 = boto3.client("s3")
        print(f"[s3] Downloading {key} from bucket '{S3_BUCKET_NAME}' to '{local_path}'...")
        s3.download_file(S3_BUCKET_NAME, key, local_path)
        print(f"[s3] Downloaded {key} successfully.")
    except Exception as e:
        print(f"[s3] Failed to download {key} from S3: {e}")

def upload_models_to_s3() -> None:
    """Upload model weights and embeddings pkl files to S3 if S3_BUCKET_NAME is configured."""
    if not S3_BUCKET_NAME:
        print("[s3] S3_BUCKET_NAME environment variable not set. Cannot upload to S3.")
        return

    import boto3
    from botocore.exceptions import ClientError
    s3 = boto3.client("s3")

    targets = [
        ("models/anime_model.pth", _model_path),
        ("processed/anime_embeddings.pkl", _pkl_path),
    ]

    for key, local_path in targets:
        if not os.path.exists(local_path):
            print(f"[s3] Local file {local_path} does not exist. Cannot upload.")
            continue
        try:
            print(f"[s3] Uploading {local_path} to S3 key '{key}' in bucket '{S3_BUCKET_NAME}'...")
            s3.upload_file(local_path, S3_BUCKET_NAME, key)
            print(f"[s3] Successfully uploaded {key} to S3.")
        except ClientError as e:
            print(f"[s3] Error uploading {key} to S3: {e}")
        except Exception as e:
            print(f"[s3] Unexpected error uploading {key}: {e}")

# Load SentenceTransformer model once at module level
from sentence_transformers import SentenceTransformer

sentence_transformer = SentenceTransformer("all-MiniLM-L6-v2")

anime_model = AnimeAutoEncoder(input_dim=384, latent_dim=32).to(device)
_model_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "models",
    "anime_model.pth",
)
if os.path.exists(_model_path):
    anime_model.load_state_dict(torch.load(_model_path, map_location=device))
anime_model.eval()

# Load 15,000 dataset embeddings
_pkl_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "processed",
    "anime_embeddings.pkl",
)

_download_from_s3_if_needed("processed/anime_embeddings.pkl", _pkl_path)

anime_data_map = {}
latent_ids = []
latent_matrix = None

if os.path.exists(_pkl_path):
    with open(_pkl_path, 'rb') as f:
        anime_embeddings = pickle.load(f)
        
    for k, v in anime_embeddings.items():
        anime_data_map[str(k)] = v  # Ensure keys are strings
        latent_ids.append(str(k))
        
    if latent_ids:
        # Move to CPU tensor for fast batch cosine similarity 
        latent_matrix = torch.tensor(
            np.array([anime_data_map[aid]['embedding'] for aid in latent_ids]),
            dtype=torch.float32
        )

# In-memory cache for dynamically computed cold-start embeddings
cold_start_embeddings = {}

# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def get_or_compute_embedding(anime_id: int, metadata: dict = None) -> Tuple[Optional[np.ndarray], Optional[str], Optional[list]]:
    """
    Returns the 32-d latent embedding for an anime, its title, and its genres.
    If the anime is not in the precomputed set, it fetches metadata and computes
    the embedding on the fly using the SentenceTransformer and AutoEncoder.
    
    Returns (embedding, title, genres). 
    If metadata is too thin, embedding will be None.
    """
    str_id = str(anime_id)
    
    # 1. Check precomputed
    if str_id in anime_data_map:
        return (
            anime_data_map[str_id]['embedding'], 
            anime_data_map[str_id]['title'], 
            anime_data_map[str_id].get('genres', [])
        )
        
    # 2. Check cold-start cache
    if str_id in cold_start_embeddings:
        return (
            cold_start_embeddings[str_id]['embedding'],
            cold_start_embeddings[str_id]['title'],
            cold_start_embeddings[str_id]['genres']
        )
        
    # 3. Fetch metadata if missing
    if not metadata:
        metadata = fetch_anime_metadata(anime_id)
        
    if not metadata:
        return None, None, []
        
    # 4. Map AniList metadata to our expected string format
    # description -> synopsis, genres array -> string, tags array -> string
    title_obj = metadata.get("title") or {}
    if isinstance(title_obj, str):
        title = title_obj
    else:
        title = title_obj.get("english") or title_obj.get("romaji") or "Unknown Title"
        
    synopsis = (metadata.get("description") or "").strip()
    
    genres_list = metadata.get("genres") or []
    genres_str = " ".join(genres_list).strip()
    
    tags_list = metadata.get("tags") or []
    tags_str = " ".join([t.get("name", "") for t in tags_list]).strip()
    
    combined_text = f"{synopsis} {genres_str} {tags_str}"
    
    # 5. Check for thin metadata (less than 20 words/tokens after basic splitting)
    import re
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', combined_text.lower())
    tokens = cleaned.split()
    
    if len(tokens) < 20:
        print(f"[cold-start] Anime {anime_id} has thin metadata ({len(tokens)} tokens). Skipping embedding.")
        return None, title, genres_list
        
    # 6. Transform and encode using SentenceTransformer
    if sentence_transformer is None or anime_model is None:
        print("[cold-start] Model or SentenceTransformer not loaded.")
        return None, title, genres_list
        
    dense_vec = sentence_transformer.encode([combined_text])
    feature_tensor = torch.tensor(dense_vec, dtype=torch.float32).to(device)
    
    with torch.no_grad():
        embedding = anime_model.encode(feature_tensor).cpu().numpy()[0]
        
    # 7. Cache it
    cold_start_embeddings[str_id] = {
        'embedding': embedding,
        'title': title,
        'genres': genres_list
    }
    
    return embedding, title, genres_list
