import sys; import os; import torch
sys.path.append(os.path.abspath('.'))
from models.anime_dnn import AnimeAutoEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import csv

# Replicate train_anime.py data load
texts = []
with open('data/raw/top_15000_anime.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        syn = (row.get('synopsis') or '').strip()
        gen = (row.get('genres') or '').strip()
        thm = (row.get('themes') or '').strip()
        if not syn and not gen: continue
        anime_id = int(row.get('anime_id', 0))
        if anime_id == 0: continue
        texts.append(f"{syn} {gen} {thm}")

vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
tf_idf_matrix = vectorizer.fit_transform(texts).toarray()
tf_idf_features = torch.tensor(tf_idf_matrix, dtype=torch.float32)

from sklearn.model_selection import train_test_split
X_train, X_val = train_test_split(tf_idf_features, test_size=0.2, random_state=42)

model = AnimeAutoEncoder(input_dim=1000, latent_dim=32)
model.load_state_dict(torch.load('data/models/anime_model.pth', map_location='cpu'))
model.eval()

with torch.no_grad():
    import random
    random.seed(42)
    indices = random.sample(range(len(X_val)), min(5, len(X_val)))
    for idx in indices:
        orig = X_val[idx]
        recon = model(orig.unsqueeze(0)).squeeze(0)
        nonzero_idx = orig.nonzero(as_tuple=True)[0]
        compare_idx = nonzero_idx[:5]
        print(f'Sample {idx} nonzero feature comparison (Orig vs Recon):')
        for i in compare_idx:
            print(f'  Feature {i.item()}: {orig[i].item():.6f} vs {recon[i].item():.6f}')
