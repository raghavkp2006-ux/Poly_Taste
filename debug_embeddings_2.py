import os
import sys
import csv
import torch
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
sys.path.append(os.path.abspath('.'))
from models.anime_dnn import AnimeAutoEncoder

# Load dataset
data_path = 'data/raw/top_15000_anime.csv'
anime_records = []
texts = []
with open(data_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        syn = (row.get('synopsis') or '').strip()
        gen = (row.get('genres') or '').strip()
        thm = (row.get('themes') or '').strip()
        if not syn and not gen:
            continue
        anime_id = int(row.get('anime_id', 0))
        if anime_id == 0: continue
        texts.append(f"{syn} {gen} {thm}")
        anime_records.append({'id': str(anime_id), 'title': row.get('name', '')})

# Fit TF-IDF
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
tf_idf_matrix = vectorizer.fit_transform(texts).toarray()

print('--- STEP 1: TF-IDF VECTORS (Non-zero elements) ---')
target_ids = ['21', '50631', '32245']
for aid in target_ids:
    idx = next(i for i, r in enumerate(anime_records) if r['id'] == aid)
    vec = tf_idf_matrix[idx]
    non_zeros = [(i, val) for i, val in enumerate(vec) if val > 0]
    print(f"{anime_records[idx]['title']} ({aid}): {len(non_zeros)} non-zero features")
    print(f"First 5 features: {non_zeros[:5]}\n")

print('--- STEP 3: MODEL WEIGHTS CHECKSUM ---')
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = AnimeAutoEncoder(input_dim=1000, latent_dim=32).to(device)
model_path = 'data/models/anime_model.pth'

# Hash untrained model
untrained_hash = hashlib.md5(str(model.state_dict()).encode()).hexdigest()
print(f'Untrained weights hash: {untrained_hash}')

model.load_state_dict(torch.load(model_path, map_location=device))
trained_hash = hashlib.md5(str(model.state_dict()).encode()).hexdigest()
print(f'Trained weights hash:   {trained_hash}')

# Step 4 check
print('\n--- STEP 4: EVAL MODE ---')
# The user wants to see what the state of model is IN generate_anime_embeddings.py, so I will check the actual script.
with open('scripts/generate_anime_embeddings.py', 'r') as f:
    content = f.read()
    if 'model.eval()' in content:
        print("model.eval() IS called in generate_anime_embeddings.py")
    else:
        print("model.eval() is NOT called in generate_anime_embeddings.py")
