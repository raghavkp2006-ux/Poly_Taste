import torch
import torch.nn as nn
import torch.nn.functional as F

class AnimeAutoEncoder(nn.Module):
    """
    An AutoEncoder to compress dense sentence-transformer anime features (384 dims)
    into a smaller latent space (e.g. 32 dims) for cosine similarity computation.
    """
    def __init__(self, input_dim=384, latent_dim=32):
        super(AnimeAutoEncoder, self).__init__()
        # Encoder
        self.enc1 = nn.Linear(input_dim, 128)
        self.enc2 = nn.Linear(128, latent_dim)
        
        # Decoder
        self.dec1 = nn.Linear(latent_dim, 128)
        self.dec2 = nn.Linear(128, input_dim)
        
        # Regularization
        self.dropout = nn.Dropout(0.3)

    def encode(self, x):
        x = F.relu(self.enc1(x))
        x = self.dropout(x)
        return self.enc2(x) # Latent representation

    def forward(self, x):
        latent = self.encode(x)
        x = F.relu(self.dec1(latent))
        x = self.dropout(x)
        return self.dec2(x) # Linear output, no activation
