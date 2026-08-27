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
    
    print("Computing SentenceTransformer features using all-MiniLM-L6-v2...")
    from sentence_transformers import SentenceTransformer
    st_model = SentenceTransformer("all-MiniLM-L6-v2")
    dense_embeddings = st_model.encode(texts, show_progress_bar=True, batch_size=64)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    print("Loading trained AnimeAutoEncoder (input_dim=384)...")
    model = AnimeAutoEncoder(input_dim=384, latent_dim=32).to(device)
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'models', 'anime_model.pth')
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}. Train the model first.")
        return
        
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()  # Critical: disables dropout to ensure deterministic embeddings
    
    print("Extracting 32-dim latent embeddings...")
    embeddings_dict = {}
    
    batch_size = 1000
    with torch.no_grad():
        for i in range(0, len(anime_records), batch_size):
            batch_texts = dense_embeddings[i:i+batch_size]
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
