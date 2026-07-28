import torch
import torch.nn as nn
import torch.optim as optim
import os
import sys
import json
import csv
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

# Add the project root to sys.path so we can import from models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.anime_dnn import AnimeAutoEncoder

def train_model():
    print("Loading real anime data...")
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw', 'top_15000_anime.csv')
    if not os.path.exists(data_path):
        print(f"Error: Could not find {data_path}.")
        return
        
    total_records = 0
    usable_records = 0
    texts = []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_records += 1
            syn = (row.get('synopsis') or '').strip()
            gen = (row.get('genres') or '').strip()
            thm = (row.get('themes') or '').strip()
            
            if not syn and not gen:
                continue
                
            usable_records += 1
            texts.append(f"{syn} {gen} {thm}")
            
    print(f"Raw records: {total_records}")
    print(f"Usable records after dropping missing: {usable_records}")
    
    print("Computing TF-IDF features...")
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    tf_idf_matrix = vectorizer.fit_transform(texts).toarray()
    
    # Convert to PyTorch tensor
    tf_idf_features = torch.tensor(tf_idf_matrix, dtype=torch.float32)
    num_samples, input_dimension = tf_idf_features.shape
    
    print(f"Feature shape: {num_samples} samples, {input_dimension} features")
    
    num_zeros = (tf_idf_matrix == 0).sum()
    total_elements = tf_idf_matrix.size
    sparsity = (num_zeros / total_elements) * 100
    print(f"Dataset size check: Loaded {num_samples} records. This is the dataset size feeding into the model.")
    print(f"Sparsity check: {sparsity:.2f}% of the TF-IDF feature matrix is zero-valued.")

    X_train, X_val = train_test_split(tf_idf_features, test_size=0.2, random_state=42)
    print(f"Split into {len(X_train)} train and {len(X_val)} validation samples.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    print("Initializing Anime AutoEncoder...")
    model = AnimeAutoEncoder(input_dim=input_dimension, latent_dim=32).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    print("Training model...")
    epochs = 200
    
    # Move features to device once since it's full-batch training
    X_train = X_train.to(device)
    X_val = X_val.to(device)
    
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        # AutoEncoder tries to reconstruct its input
        outputs = model(X_train)
        loss = criterion(outputs, X_train)
        
        loss.backward()
        optimizer.step()
        
        # Eval val loss
        model.eval()
        with torch.no_grad():
            val_outputs = model(X_val)
            val_loss = criterion(val_outputs, X_val)
        
        if (epoch + 1) in [1, 10, 50, 100, 150, 200]:
            # Also check latent diversity (detect mode collapse early)
            with torch.no_grad():
                sample_latent = model.encode(X_val[:100])
                latent_std = sample_latent.std(dim=0).mean().item()
            print(f"Epoch [{epoch+1}/{epochs}], Train Loss: {loss.item():.6f} | Val Loss: {val_loss.item():.6f} | Latent Std: {latent_std:.6f}")

    # Save the model
    os.makedirs('data/models', exist_ok=True)
    model_path = 'data/models/anime_model.pth'
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")

    # Save the fitted TfidfVectorizer so embedding generation uses the
    # exact same vocabulary and IDF weights (prevents mode collapse)
    vectorizer_path = 'data/models/tfidf_vectorizer.pkl'
    with open(vectorizer_path, 'wb') as vf:
        pickle.dump(vectorizer, vf)
    print(f"TfidfVectorizer saved to {vectorizer_path}")

    print("\n--- Reconstruction Quality Check (Validation Set) ---")
    model.eval()
    with torch.no_grad():
        import random
        random.seed(42)
        indices = random.sample(range(len(X_val)), min(5, len(X_val)))
        for idx in indices:
            orig = X_val[idx]
            recon = model(orig.unsqueeze(0)).squeeze(0)
            nonzero_idx = orig.nonzero(as_tuple=True)[0]
            if len(nonzero_idx) == 0:
                print(f"Sample {idx}: Original is entirely zero.")
                continue
            
            compare_idx = nonzero_idx[:5]
            print(f"Sample {idx} nonzero feature comparison (Orig vs Recon):")
            for i in compare_idx:
                print(f"  Feature {i.item()}: {orig[i].item():.6f} vs {recon[i].item():.6f}")

if __name__ == "__main__":
    train_model()
