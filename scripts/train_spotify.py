"""
train_spotify.py — Train the SpotifySimilarityDNN.

Background
----------
The /audio-features Spotify API endpoint was deprecated for new Developer apps
in November 2024, making the DNN path a legacy/opt-in feature.  The
genre-profile content-scoring path (routers/spotify.py → /spotify/recommendations)
is now the primary recommendation engine and does not use this model.

This script exists to produce a usable ``data/models/spotify_model.pth`` for
anyone who still has /audio-features access (pre-Nov-2024 apps) or wants to
experiment with the DNN path.

Training signal
---------------
Rather than random vectors (the old behaviour), we now build genre-cluster
pairs as a proxy for "similar / dissimilar" tracks:

  - Positive pair  (label = 1): two random feature vectors sampled from the
    same genre cluster (both vectors drawn from a normal distribution centred
    on the cluster mean).
  - Negative pair  (label = 0): two vectors drawn from *different* cluster
    centres.

This gives the model a real structural signal without requiring user-specific
co-listen data (which would need OAuth and a live dataset).

Usage
-----
    python scripts/train_spotify.py            # full training run
    python scripts/train_spotify.py --dry-run  # validate setup, no training
"""

import argparse
import os
import sys

import torch
import torch.nn as nn
import torch.optim as optim

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.spotify_dnn import SpotifySimilarityDNN

# ---------------------------------------------------------------------------
# Genre-cluster proxy signal
# ---------------------------------------------------------------------------
# Each cluster represents a broad musical genre as a rough 5-d audio feature
# centroid [danceability, energy, tempo_norm, valence, acousticness].
# Values are approximate but directionally sensible (e.g. classical is low
# energy / low danceability / high acousticness; hip-hop is high danceability).
GENRE_CLUSTERS = {
    "pop":         [0.75, 0.65, 0.60, 0.70, 0.20],
    "rock":        [0.55, 0.85, 0.75, 0.50, 0.10],
    "hip_hop":     [0.80, 0.70, 0.55, 0.55, 0.12],
    "electronic":  [0.72, 0.82, 0.80, 0.60, 0.08],
    "jazz":        [0.50, 0.45, 0.40, 0.55, 0.55],
    "classical":   [0.25, 0.25, 0.35, 0.45, 0.90],
    "folk":        [0.45, 0.40, 0.40, 0.60, 0.75],
    "r_and_b":     [0.70, 0.60, 0.55, 0.65, 0.25],
}
CLUSTER_NAMES = list(GENRE_CLUSTERS.keys())
CLUSTER_MEANS = torch.tensor(list(GENRE_CLUSTERS.values()), dtype=torch.float32)  # (8, 5)


def sample_from_cluster(cluster_idx: int, n: int, noise: float = 0.12) -> torch.Tensor:
    """Sample *n* feature vectors near cluster centre with Gaussian noise."""
    mean = CLUSTER_MEANS[cluster_idx]
    samples = mean.unsqueeze(0).expand(n, -1) + torch.randn(n, 5) * noise
    return samples.clamp(0.0, 1.0)


def generate_training_data(num_samples: int = 2000):
    """
    Build a balanced set of positive (same cluster) and negative (different
    cluster) track pairs.

    Returns
    -------
    seed_feats, candidate_feats : (N, 5) tensors
    labels                      : (N, 1) tensor, values in {0.0, 1.0}
    """
    n_clusters = len(CLUSTER_NAMES)
    half = num_samples // 2

    # --- Positive pairs ---
    pos_seed = []
    pos_cand = []
    for _ in range(half):
        c = torch.randint(0, n_clusters, (1,)).item()
        pos_seed.append(sample_from_cluster(c, 1))
        pos_cand.append(sample_from_cluster(c, 1))
    pos_seed = torch.cat(pos_seed, dim=0)
    pos_cand = torch.cat(pos_cand, dim=0)

    # --- Negative pairs (different clusters) ---
    neg_seed = []
    neg_cand = []
    for _ in range(half):
        c1, c2 = torch.randperm(n_clusters)[:2].tolist()
        neg_seed.append(sample_from_cluster(c1, 1))
        neg_cand.append(sample_from_cluster(c2, 1))
    neg_seed = torch.cat(neg_seed, dim=0)
    neg_cand = torch.cat(neg_cand, dim=0)

    seed_feats = torch.cat([pos_seed, neg_seed], dim=0)
    cand_feats = torch.cat([pos_cand, neg_cand], dim=0)
    labels = torch.cat([
        torch.ones(half, 1),
        torch.zeros(half, 1),
    ], dim=0)

    # Shuffle
    perm = torch.randperm(num_samples)
    return seed_feats[perm], cand_feats[perm], labels[perm]


def validate_setup() -> bool:
    """Check environment and imports are correct."""
    print("--- Dry run validation ---")
    print(f"PyTorch version : {torch.__version__}")
    print(f"CUDA available  : {torch.cuda.is_available()}")
    print(f"Genre clusters  : {CLUSTER_NAMES}")
    sf, cf, lb = generate_training_data(num_samples=16)
    print(f"Sample batch    : seed={sf.shape}, cand={cf.shape}, labels={lb.shape}")
    model = SpotifySimilarityDNN(input_dim=10, hidden_dim=32)
    out = model(sf[:4], cf[:4])
    print(f"Model forward   : output shape={out.shape}, values={out.detach().squeeze().tolist()}")
    print("Dry run OK — no model was saved.")
    return True


def train(num_samples: int = 2000, epochs: int = 80, lr: float = 0.005) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    print("Generating genre-cluster proxy training data...")
    seed_feats, cand_feats, labels = generate_training_data(num_samples)
    seed_feats = seed_feats.to(device)
    cand_feats = cand_feats.to(device)
    labels = labels.to(device)
    print(f"  {num_samples} pairs ({num_samples // 2} positive, {num_samples // 2} negative)")

    model = SpotifySimilarityDNN(input_dim=10, hidden_dim=32).to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    print("Training...")
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(seed_feats, cand_feats)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 20 == 0:
            with torch.no_grad():
                preds = (outputs >= 0.5).float()
                acc = (preds == labels).float().mean().item()
            print(f"  Epoch [{epoch+1:3d}/{epochs}]  loss={loss.item():.4f}  acc={acc:.3f}")

    os.makedirs("data/models", exist_ok=True)
    model_path = "data/models/spotify_model.pth"
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")
    print(
        "\nNote: This model uses genre-cluster proxy signal and is only relevant for "
        "the deprecated /recommend/{track_id} endpoint (requires Spotify /audio-features "
        "access). The primary recommendation path is GET /spotify/recommendations."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SpotifySimilarityDNN")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate setup and data pipeline without actually training.",
    )
    parser.add_argument("--samples", type=int, default=2000, help="Training pair count (default: 2000)")
    parser.add_argument("--epochs", type=int, default=80, help="Training epochs (default: 80)")
    parser.add_argument("--lr", type=float, default=0.005, help="Learning rate (default: 0.005)")
    args = parser.parse_args()

    if args.dry_run:
        validate_setup()
    else:
        train(num_samples=args.samples, epochs=args.epochs, lr=args.lr)
