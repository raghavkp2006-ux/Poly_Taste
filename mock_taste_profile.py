import os
import unittest.mock

os.environ["USE_LOCAL_DB"] = "true"
from services.anime_recommender import anime_data_map

sample_ids = list(anime_data_map.keys())[:10]

mock_anime_list = [
    # Explicit rating - high weight
    {"mal_id": sample_ids[0], "score": 9.0, "status": "COMPLETED", "title": anime_data_map[sample_ids[0]]["title"]},
    {"mal_id": sample_ids[1], "score": 8.0, "status": "CURRENT", "title": anime_data_map[sample_ids[1]]["title"]},
    
    # Unrated but completed - new logic applies here (weight 0.5 * _ANILIST_WEIGHT)
    {"mal_id": sample_ids[2], "score": 0.0, "status": "COMPLETED", "title": anime_data_map[sample_ids[2]]["title"]},
    {"mal_id": sample_ids[3], "score": 0.0, "status": "COMPLETED", "title": anime_data_map[sample_ids[3]]["title"]},
    
    # Unrated and currently watching - still skipped
    {"mal_id": sample_ids[4], "score": 0.0, "status": "CURRENT", "title": anime_data_map[sample_ids[4]]["title"]},
]

_ANILIST_WEIGHT = 2.0
old_profile = {}
new_profile = {}

for entry in mock_anime_list:
    status = entry["status"]
    score = entry["score"]
    mal_id = str(entry["mal_id"])
    
    genres = anime_data_map[mal_id].get("genres", [])
    
    # Old logic
    if status in {"CURRENT", "COMPLETED", "REPEATING"}:
        if score > 0:
            weight_old = (score / 10.0) * _ANILIST_WEIGHT
            for g in genres:
                old_profile[g.lower()] = old_profile.get(g.lower(), 0.0) + weight_old
    
    # New logic
    if status in {"CURRENT", "COMPLETED", "REPEATING"}:
        if score > 0:
            weight_new = (score / 10.0) * _ANILIST_WEIGHT
        elif status == "COMPLETED" and score == 0:
            weight_new = 0.5 * _ANILIST_WEIGHT
        else:
            continue
            
        for g in genres:
            new_profile[g.lower()] = new_profile.get(g.lower(), 0.0) + weight_new

print(f"--- BEFORE ---")
print(f"Dictionary size: {len(old_profile)}")
old_sorted = sorted(old_profile.items(), key=lambda x: x[1], reverse=True)[:5]
print("Top genres:")
for k, v in old_sorted: print(f"  {k}: {v:.2f}")

print(f"\n--- AFTER ---")
print(f"Dictionary size: {len(new_profile)}")
new_sorted = sorted(new_profile.items(), key=lambda x: x[1], reverse=True)[:5]
print("Top genres:")
for k, v in new_sorted: print(f"  {k}: {v:.2f}")
