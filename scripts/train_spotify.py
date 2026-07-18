import torch
import torch.nn as nn
import torch.optim as optim
import os
import sys

# Add the project root to sys.path so we can import from models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.spotify_dnn import SpotifySimilarityDNN

def train_dummy_model():
    print("Initializing Spotify DNN...")
    model = SpotifySimilarityDNN(input_dim=10, hidden_dim=32)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    # Generate synthetic data for demonstration
    # 5 audio features: danceability, energy, tempo, valence, acousticness
    print("Generating synthetic training data...")
    num_samples = 1000
    seed_features = torch.rand(num_samples, 5)
    candidate_features = torch.rand(num_samples, 5)
    
    # Let's define the "ground truth" similarity simply as the cosine similarity 
    # between the two random vectors (just so the model learns a real function)
    cos = nn.CosineSimilarity(dim=1, eps=1e-6)
    target_similarity = (cos(seed_features, candidate_features) + 1) / 2.0 # scale to [0, 1]
    target_similarity = target_similarity.view(-1, 1)

    print("Training model...")
    epochs = 50
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(seed_features, candidate_features)
        loss = criterion(outputs, target_similarity)
        loss.backward()
        optimizer.step()
        
        if (epoch+1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

    # Save the model
    os.makedirs('data/models', exist_ok=True)
    model_path = 'data/models/spotify_model.pth'
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_dummy_model()
