import sys
import os
import pickle
import json
import torch
import torch.nn as nn
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load embeddings
pkl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed', 'anime_embeddings.pkl')
with open(pkl_path, 'rb') as f:
    anime_embeddings = pickle.load(f)

# Build lookup
anime_data_map = {}
latent_ids = []
for k, v in anime_embeddings.items():
    anime_data_map[k] = v
    latent_ids.append(k)

latent_matrix = torch.tensor(
    np.array([anime_data_map[aid]['embedding'] for aid in latent_ids]),
    dtype=torch.float32
)

# Find One Piece, Bleach, Naruto Shippuuden IDs
target_titles = ['One Piece', 'Bleach', 'Naruto: Shippuuden']
liked_ids = []
for aid, info in anime_data_map.items():
    for t in target_titles:
        if info['title'].lower() == t.lower():
            liked_ids.append(aid)
            print(f"Found: {info['title']} (ID: {aid}, genres: {info['genres']})")

if len(liked_ids) < len(target_titles):
    # try substring match for remaining
    found_lower = set(anime_data_map[x]['title'].lower() for x in liked_ids)
    for aid, info in anime_data_map.items():
        for t in target_titles:
            if t.lower() in info['title'].lower() and info['title'].lower() not in found_lower:
                liked_ids.append(aid)
                found_lower.add(info['title'].lower())
                print(f"Found (substring): {info['title']} (ID: {aid}, genres: {info['genres']})")

print(f"\nUsing liked_ids: {liked_ids}")

# Compute taste vector
vectors = [anime_data_map[aid]['embedding'] for aid in liked_ids]
taste_vector = torch.tensor(vectors, dtype=torch.float32).mean(dim=0, keepdim=True)

# Cosine similarity
cos = nn.CosineSimilarity(dim=1, eps=1e-6)
similarities = cos(taste_vector, latent_matrix)

# Top results
top_k = min(20, len(latent_ids))
scores, indices = torch.topk(similarities, top_k)

liked_set = set(liked_ids)
print(f"\n--- Top Recommendations (UNROUNDED similarity scores) ---")
count = 0
for score, idx in zip(scores, indices):
    idx_val = idx.item()
    aid = latent_ids[idx_val]
    if aid in liked_set:
        print(f"  [LIKED] {anime_data_map[aid]['title']} | score={score.item():.10f} | genres={anime_data_map[aid]['genres']}")
        continue
    count += 1
    print(f"  #{count} {anime_data_map[aid]['title']} | score={score.item():.10f} | genres={anime_data_map[aid]['genres']}")
    if count >= 10:
        break

# Score range stats
print(f"\n--- Score Statistics (across all {len(latent_ids)} anime) ---")
print(f"Max similarity: {similarities.max().item():.10f}")
print(f"Min similarity: {similarities.min().item():.10f}")
print(f"Mean similarity: {similarities.mean().item():.10f}")
print(f"Std similarity: {similarities.std().item():.10f}")
print(f"Median similarity: {similarities.median().item():.10f}")

# Check: are all scores identical (mode collapse)?
unique_scores = len(torch.unique(torch.round(similarities * 10000)))
print(f"Unique score buckets (rounded to 4 decimal places): {unique_scores}")
if unique_scores < 10:
    print("WARNING: Very few unique scores — mode collapse may still be present!")
else:
    print("OK: Scores show healthy variation — mode collapse is FIXED!")
