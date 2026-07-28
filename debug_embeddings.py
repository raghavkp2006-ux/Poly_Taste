import pickle
import torch
import torch.nn as nn
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Load embeddings
with open('data/processed/anime_embeddings.pkl', 'rb') as f:
    data = pickle.load(f)

# Step 2: Print embeddings for One Piece (21), Komi-san (50631), and Kuromukuro (32245)
print('--- STEP 2: EMBEDDING VECTORS ---')
for aid in ['21', '50631', '32245']:
    print(f"{data[aid]['title']} ({aid}):")
    print(data[aid]['embedding'])
    print()

# Step 4: Taste vector
liked_ids = ['21', '41467', '1735']
vectors = [np.array(data[aid]['embedding']) for aid in liked_ids]
taste_vector = torch.tensor(vectors, dtype=torch.float32).mean(dim=0, keepdim=True)
print('--- STEP 4: TASTE VECTOR ---')
print(taste_vector.numpy())
print()

# Step 1: Raw Unrounded Cosine Similarity Scores
print('--- STEP 1: RAW COSINE SIMILARITY SCORES ---')
latent_ids = list(data.keys())
latent_matrix = torch.tensor(np.array([data[aid]['embedding'] for aid in latent_ids]), dtype=torch.float32)
cos = nn.CosineSimilarity(dim=1, eps=1e-6)
similarities = cos(taste_vector, latent_matrix)
top_k = min(10 + len(liked_ids), len(latent_ids))
scores, indices = torch.topk(similarities, top_k)

liked_set = set(liked_ids)
count = 0
for score, idx in zip(scores, indices):
    idx = idx.item()
    aid = latent_ids[idx]
    if aid in liked_set:
        continue
    print(f"{data[aid]['title']} ({aid}): {score.item():.15f}")
    count += 1
    if count == 10:
        break
