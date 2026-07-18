import torch
import torch.nn as nn
import torch.optim as optim
import os
import sys
import json
from sklearn.feature_extraction.text import TfidfVectorizer

# Add the project root to sys.path so we can import from models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.anime_dnn import AnimeAutoEncoder

def train_model():
    print("Loading real anime data...")
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw', 'anime_catalog.json')
    if not os.path.exists(data_path):
        print(f"Error: Could not find {data_path}. Run jikan_client.py first.")
        return
        
    with open(data_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
        
    print(f"Loaded {len(catalog)} anime records.")
    
    # Extract text (synopsis + genres) for TF-IDF
    texts = [f"{anime.get('synopsis', '')} {' '.join(anime.get('genres', []))}" for anime in catalog]
    
    print("Computing TF-IDF features...")
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    tf_idf_matrix = vectorizer.fit_transform(texts).toarray()
    
    # Convert to PyTorch tensor
    tf_idf_features = torch.tensor(tf_idf_matrix, dtype=torch.float32)
    num_samples, input_dimension = tf_idf_features.shape
    
    print(f"Feature shape: {num_samples} samples, {input_dimension} features")

    print("Initializing Anime AutoEncoder...")
    model = AnimeAutoEncoder(input_dim=input_dimension, latent_dim=32)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.005)

    print("Training model...")
    epochs = 100
    for epoch in range(epochs):
        optimizer.zero_grad()
        # AutoEncoder tries to reconstruct its input
        outputs = model(tf_idf_features)
        loss = criterion(outputs, tf_idf_features)
        loss.backward()
        optimizer.step()
        
        if (epoch+1) % 20 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

    # Save the model
    os.makedirs('data/models', exist_ok=True)
    model_path = 'data/models/anime_model.pth'
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_model()
