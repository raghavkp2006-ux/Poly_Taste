import os
import sys
import csv
import pickle
import torch

# Add the project root to sys.path so we can import from models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.anime_dnn import AnimeAutoEncoder

def main():
    print("Loading top_15000_anime.csv...")
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw', 'top_15000_anime.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: Could not find {data_path}.")
        return

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
            if anime_id == 0:
                continue
                
            texts.append(f"{syn} {gen} {thm}")
            anime_records.append({
                'id': str(anime_id),
                'title': row.get('name', ''),
                'imageUrl': row.get('image_url', ''),
                'genres': gen
            })
            
    print(f"Loaded {len(anime_records)} usable records.")
    
    # Load the SAME fitted TfidfVectorizer used during training to guarantee
    # identical feature space (vocabulary + IDF weights). Using fit_transform()
    # with a new vectorizer would produce a different vocabulary ordering and
    # different IDF values, corrupting the autoencoder's input and causing
    # mode collapse (all embeddings ~identical).
    vectorizer_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'models', 'tfidf_vectorizer.pkl')
    if not os.path.exists(vectorizer_path):
        print(f"Error: Fitted vectorizer not found at {vectorizer_path}. Run train_anime.py first.")
        return
    
    print(f"Loading fitted TfidfVectorizer from {vectorizer_path}...")
    with open(vectorizer_path, 'rb') as vf:
        vectorizer = pickle.load(vf)
    
    print("Transforming text with pre-fitted vectorizer (transform, NOT fit_transform)...")
    tf_idf_matrix = vectorizer.transform(texts).toarray()
    
    # --- Diagnostic: print raw TF-IDF vectors for 3 specific anime ---
    diag_titles = ["One Piece", "Komi-san wa, Comyushou desu.", "Kuromukuro"]
    title_to_idx = {rec['title']: i for i, rec in enumerate(anime_records)}
    print("\n--- TF-IDF Diagnostic (raw vectors for 3 anime) ---")
    for title in diag_titles:
        # Try exact match first, then substring match
        idx = title_to_idx.get(title)
        if idx is None:
            for t, i in title_to_idx.items():
                if title.lower() in t.lower():
                    idx = i
                    title = t
                    break
        if idx is not None:
            vec = tf_idf_matrix[idx]
            nonzero_indices = vec.nonzero()[0]
            feature_names = vectorizer.get_feature_names_out()
            print(f"\n  '{title}' — {len(nonzero_indices)} nonzero features, L2 norm={sum(vec**2)**0.5:.4f}")
            top_indices = nonzero_indices[vec[nonzero_indices].argsort()[::-1][:10]]
            for fi in top_indices:
                print(f"    feature[{fi}] '{feature_names[fi]}' = {vec[fi]:.6f}")
        else:
            print(f"\n  '{title}' — NOT FOUND in dataset")
    print("--- End TF-IDF Diagnostic ---\n")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    print("Loading trained AnimeAutoEncoder...")
    model = AnimeAutoEncoder(input_dim=1000, latent_dim=32).to(device)
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'models', 'anime_model.pth')
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}. Train the model first.")
        return
        
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()  # Critical: disables dropout to ensure deterministic embeddings
    
    print("Extracting latent embeddings...")
    embeddings_dict = {}
    
    batch_size = 1000
    with torch.no_grad():
        for i in range(0, len(anime_records), batch_size):
            batch_texts = tf_idf_matrix[i:i+batch_size]
            batch_tensor = torch.tensor(batch_texts, dtype=torch.float32).to(device)
            latent_batch = model.encode(batch_tensor).cpu().numpy()
            
            for j, latent in enumerate(latent_batch):
                record = anime_records[i+j]
                embeddings_dict[record['id']] = {
                    'embedding': latent,
                    'title': record['title'],
                    'imageUrl': record['imageUrl'],
                    'genres': record['genres']
                }
                
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'anime_embeddings.pkl')
    
    with open(out_path, 'wb') as f:
        pickle.dump(embeddings_dict, f)
        
    print(f"Successfully saved {len(embeddings_dict)} embeddings to {out_path}.")

if __name__ == '__main__':
    main()
