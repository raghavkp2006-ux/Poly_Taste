import torch
import torch.nn as nn
import torch.nn.functional as F

class SpotifySimilarityDNN(nn.Module):
    """
    A simple Deep Neural Network that takes the features of a seed track (5 dims)
    and a candidate track (5 dims), concatenates them, and outputs a similarity score (0 to 1).
    """
    def __init__(self, input_dim=10, hidden_dim=32):
        super(SpotifySimilarityDNN, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, 1)

    def forward(self, seed_features, candidate_features):
        x = torch.cat([seed_features, candidate_features], dim=-1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = torch.sigmoid(self.fc3(x)) # Output similarity score between 0 and 1
        return x
