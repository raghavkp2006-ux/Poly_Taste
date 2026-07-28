import sys
import os
import pickle

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from routers.anime import get_recommendations, AnimeRecRequest

with open('data/processed/anime_embeddings.pkl', 'rb') as f:
    data = pickle.load(f)

# Use some known IDs from the dataset
ids = list(data.keys())[:3]
print(f"Using liked_ids: {ids}")
for aid in ids:
    print(f"- {data[aid]['title']} ({data[aid]['genres']})")

req = AnimeRecRequest(liked_ids=ids)
res = get_recommendations(req, limit=5)

print("\nRecommendations:")
for rec in res['recommendations']:
    print(f"- {rec['title']} (Score: {rec['score']}) [Reason: {rec['reason']}]")
